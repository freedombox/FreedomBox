# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for filesystem snapshots."""

import os
import signal
import subprocess

import augeas
import dbus

from plinth.actions import privileged

FSTAB = '/etc/fstab'
AUG_FSTAB = '/files/etc/fstab'
DEFAULT_FILE = '/etc/default/snapper'


@privileged
def setup(old_version: int):
    """Configure snapper."""
    # Check if root config exists.
    command = ['snapper', 'list-configs']
    process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    output = process.stdout.decode()

    # Create root config if needed.
    if 'root' not in output:
        command = ['snapper', 'create-config', '/']
        subprocess.run(command, check=True)

    _add_fstab_entry('/')
    if old_version == 0:
        _set_default_config()
    elif old_version <= 3:
        _migrate_config_from_version_3()
    else:
        pass  # After version 4 and above don't reset configuration


def _migrate_config_from_version_3():
    """Upgrade configuration from version <=3.

    - This configuration was not using ranges for limits which would make free
      space setting unused.
    - Force set yes to cleanups.
    - Reset all number cleanup settings.
    - Make free space setting 30% by default instead of 20%.

    """
    config = _get_config()

    def convert_to_range(key):
        value = config[key]
        value = value if '-' in value else '0-{}'.format(value)
        return '{}={}'.format(key, value)

    command = [
        'snapper',
        'set-config',
        'TIMELINE_CLEANUP=yes',
        'TIMELINE_MIN_AGE=0',
        convert_to_range('TIMELINE_LIMIT_HOURLY'),
        convert_to_range('TIMELINE_LIMIT_DAILY'),
        convert_to_range('TIMELINE_LIMIT_WEEKLY'),
        convert_to_range('TIMELINE_LIMIT_MONTHLY'),
        convert_to_range('TIMELINE_LIMIT_YEARLY'),
        'NUMBER_CLEANUP=yes',
        'NUMBER_MIN_AGE=0',
        'NUMBER_LIMIT=0-100',
        'NUMBER_LIMIT_IMPORTANT=0-20',
        'EMPTY_PRE_POST_MIN_AGE=0',
        'FREE_LIMIT=0.3',
    ]
    subprocess.run(command, check=True)


def _set_default_config():
    command = [
        'snapper',
        'set-config',
        'TIMELINE_CLEANUP=yes',
        'TIMELINE_CREATE=yes',
        'TIMELINE_MIN_AGE=0',
        'TIMELINE_LIMIT_HOURLY=0-10',
        'TIMELINE_LIMIT_DAILY=0-3',
        'TIMELINE_LIMIT_WEEKLY=0-2',
        'TIMELINE_LIMIT_MONTHLY=0-2',
        'TIMELINE_LIMIT_YEARLY=0-0',
        'NUMBER_CLEANUP=yes',
        'NUMBER_MIN_AGE=0',
        'NUMBER_LIMIT=0-100',
        'NUMBER_LIMIT_IMPORTANT=0-20',
        'EMPTY_PRE_POST_MIN_AGE=0',
        'FREE_LIMIT=0.3',
    ]
    subprocess.run(command, check=True)


def _add_fstab_entry(mount_point):
    """Add mountpoint for subvolumes."""
    snapshots_mount_point = os.path.join(mount_point, '.snapshots')

    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Fstab/lens', 'Fstab.lns')
    aug.set('/augeas/load/Fstab/incl[last() + 1]', FSTAB)
    aug.load()

    spec = None
    for entry in aug.match(AUG_FSTAB + '/*'):
        entry_mount_point = aug.get(entry + '/file')
        if entry_mount_point == snapshots_mount_point:
            return

        if entry_mount_point == mount_point and \
           aug.get(entry + '/vfstype') == 'btrfs':
            spec = aug.get(entry + '/spec')

    if spec:
        aug.set(AUG_FSTAB + '/01/spec', spec)
        aug.set(AUG_FSTAB + '/01/file', snapshots_mount_point)
        aug.set(AUG_FSTAB + '/01/vfstype', 'btrfs')
        aug.set(AUG_FSTAB + '/01/opt', 'subvol')
        aug.set(AUG_FSTAB + '/01/opt/value', '.snapshots')
        aug.set(AUG_FSTAB + '/01/dump', '0')
        aug.set(AUG_FSTAB + '/01/passno', '1')
        aug.save()


def _parse_number(number):
    """Parse the char following the number and return status of snapshot."""
    is_default = number[-1] in ('+', '*')
    is_active = number[-1] in ('-', '*')
    return number.strip('-+*'), is_default, is_active


@privileged
def list_() -> list[dict[str, str]]:
    """List snapshots."""
    process = subprocess.run(['snapper', 'list'], stdout=subprocess.PIPE,
                             check=True)
    lines = process.stdout.decode().splitlines()

    keys = ('number', 'is_default', 'is_active', 'type', 'pre_number', 'date',
            'user', 'cleanup', 'description')
    snapshots = []
    for line in lines[2:]:
        parts = [part.strip() for part in line.split('|')]
        parts = list(_parse_number(parts[0])) + parts[1:]
        snapshot = dict(zip(keys, parts))
        # Snapshot 0 always represents the current system, it need not be
        # listed and cannot be deleted.
        if snapshot['number'] != '0':
            snapshots.append(snapshot)

    snapshots.reverse()
    return snapshots


def _get_default_snapshot():
    """Return the default snapshot by looking at default subvolume."""
    command = ['btrfs', 'subvolume', 'get-default', '/']
    process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    output = process.stdout.decode()

    output_parts = output.split()
    if len(output_parts) >= 9:
        path = output.split()[8]
        path_parts = path.split('/')
        if len(path_parts) == 3 and path_parts[0] == '.snapshots':
            return path_parts[1]

    return None


@privileged
def disable_apt_snapshot(state: str):
    """Set flag to Enable/Disable apt software snapshots in config files."""
    # Initialize Augeas
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DEFAULT_FILE)
    aug.load()

    aug.set('/files' + DEFAULT_FILE + '/DISABLE_APT_SNAPSHOT', state)
    aug.save()


@privileged
def create():
    """Create snapshot."""
    command = ['snapper', 'create', '--description', 'manually created']
    subprocess.run(command, check=True)


@privileged
def delete(number: str):
    """Delete a snapshot by number."""
    command = ['snapper', 'delete', number]
    subprocess.run(command, check=True)


@privileged
def set_config(config: list[str]):
    """Set snapper configuration."""
    command = ['snapper', 'set-config'] + config
    subprocess.run(command, check=True)


def _get_config():
    command = ['snapper', 'get-config']
    process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    lines = process.stdout.decode().splitlines()
    config = {}
    for line in lines[2:]:
        parts = [part.strip() for part in line.split('|')]
        config[parts[0]] = parts[1]
    return config


@privileged
def get_config() -> dict[str, str]:
    """Return snapper configuration."""
    return _get_config()


@privileged
def kill_daemon():
    """Kill the snapper daemon.

    This is generally not necessary because we do configuration changes via
    snapperd. However, when the configuration is restored from a backup. We
    need to kill the daemon to reload configuration.

    Ideally, we should be able to reload/terminate the service using systemd.
    """
    bus = dbus.SystemBus()

    dbus_object = bus.get_object('org.freedesktop.DBus', '/')
    dbus_interface = dbus.Interface(dbus_object,
                                    dbus_interface='org.freedesktop.DBus')
    try:
        pid = dbus_interface.GetConnectionUnixProcessID('org.opensuse.Snapper')
    except dbus.exceptions.DBusException:
        pass
    else:
        os.kill(pid, signal.SIGTERM)


@privileged
def rollback(number: str):
    """Rollback to snapshot."""
    # "ambit" is not very well documented by snapper. Default ambit is "auto"
    # which errors out if default subvolume is not yet set on the filesystem.
    # If set, then it acts as "transactional" ambit if the default snapshot is
    # readonly, otherwise it acts as "classic". The "classic" behavior is the
    # one described snapper(8) man page for rollback behavior. The classic
    # behavior when a snapshot number to rollback to is provided is the
    # behavior that we desire.
    command = ['snapper', '--ambit', 'classic', 'rollback', number]
    subprocess.run(command, check=True)
