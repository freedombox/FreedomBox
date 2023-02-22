# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for samba."""

import configparser
import os
import shutil
import subprocess

from plinth.actions import privileged

SHARES_CONF_BACKUP_FILE = '/var/lib/plinth/backups-data/samba-shares-dump.conf'
DEFAULT_FILE = '/etc/default/samba'

CONF_PATH = '/etc/samba/smb-freedombox.conf'
CONF = r'''
#
# This file is managed and overwritten by Plinth.  If you wish to manage
# Samba yourself, disable Samba in Plinth, remove this file and remove
# line with --configfile parameter in /etc/default/samba.
#
# Configuration parameters which differ from Debian default configuration
# are commented. To view configured samba shares use command `net conf list`.
#

[global]
   workgroup = WORKGROUP
   log file = /var/log/samba/log.%m
   max log size = 1000
   logging = file
   panic action = /usr/share/samba/panic-action %d
   server role = standalone server
   #obey pam restrictions = yes
   #unix password sync = yes
   #passwd program = /usr/bin/passwd %u
   #passwd chat = *Enter\snew\s*\spassword:* %n\n *Retype\snew\s*\spassword:* %n\n *password\supdated\ssuccessfully* .
   #pam password change = yes
   map to guest = bad user
   # connection inactivity timeout in minutes
   deadtime = 5
   # enable registry based shares
   registry shares = yes
   # Make sure Samba isn't available over the Internet.
   # https://en.wikipedia.org/wiki/localhost
   # https://en.wikipedia.org/wiki/Private_network
   # https://en.wikipedia.org/wiki/Link-local_address
   # https://en.wikipedia.org/wiki/Unique_local_address
   access control = yes
   hosts allow = 127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 [::1] [fc00::]/7 [fe80::]
   hosts deny = all
'''  # noqa: E501


def _close_share(share_name):
    """Disconnect all samba users who are connected to the share."""
    subprocess.check_call(['smbcontrol', 'smbd', 'close-share', share_name])


def _conf_command(parameters, **kwargs):
    """Run samba configuration registry command."""
    subprocess.check_call(['net', 'conf'] + parameters, **kwargs)


def _create_share(mount_point, share_type, windows_filesystem=False):
    """Create samba public, group and private shares."""
    if share_type == 'open':
        subdir = 'open_share'
    elif share_type == 'group':
        subdir = 'group_share'
    elif share_type == 'home':
        subdir = 'homes'

    shares_path = _get_shares_path(mount_point)
    share_path = os.path.join(mount_point, shares_path, subdir)
    os.makedirs(share_path, exist_ok=True)

    # FAT and NTFS partitions don't support setting permissions
    if not windows_filesystem:
        if share_type in ['open', 'group']:
            _set_share_permissions(share_path)
        else:
            shutil.chown(share_path, group='users')
            os.chmod(share_path, 0o0775)

    share_name = _create_share_name(mount_point)

    if share_type == 'open':
        _define_open_share(share_name, share_path, windows_filesystem)
    elif share_type == 'group':
        _define_group_share(share_name + '_group', share_path,
                            windows_filesystem)
    elif share_type == 'home':
        _define_homes_share(share_name + '_home', share_path)


def _create_share_name(mount_point):
    """Create a share name."""
    share_name = os.path.basename(mount_point)
    if not share_name:
        share_name = 'disk'

    return share_name


def _define_open_share(name, path, windows_filesystem=False):
    """Define an open samba share."""
    try:
        _conf_command(['delshare', name], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass
    _conf_command(['addshare', name, path, 'writeable=y', 'guest_ok=y'])
    if not windows_filesystem:
        _conf_command(['setparm', name, 'force group', 'freedombox-share'])
        _conf_command(['setparm', name, 'inherit permissions', 'yes'])


def _define_group_share(name, path, windows_filesystem=False):
    """Define a group samba share."""
    try:
        _conf_command(['delshare', name], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass
    _conf_command(['addshare', name, path, 'writeable=y', 'guest_ok=n'])
    _conf_command(['setparm', name, 'valid users', '@freedombox-share @admin'])
    if not windows_filesystem:
        _conf_command(['setparm', name, 'force group', 'freedombox-share'])
        _conf_command(['setparm', name, 'inherit permissions', 'yes'])


def _define_homes_share(name, path):
    """Define a samba share for private homes."""
    try:
        _conf_command(['delshare', name], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass
    userpath = os.path.join(path, '%u')
    _conf_command(['addshare', name, userpath, 'writeable=y', 'guest_ok=n'])
    _conf_command(['setparm', name, 'valid users', '@freedombox-share @admin'])
    _conf_command(
        ['setparm', name, 'preexec', 'mkdir -p -m 755 {}'.format(userpath)])


def _get_mount_point(path):
    """Get the mount point where the share is."""
    subpath = 'FreedomBox/shares/'
    if '/var/lib/freedombox/shares/' in path:
        if os.path.ismount(path.split('lib/freedombox/shares/')[0]):
            subpath = 'lib/freedombox/shares/'
        else:
            subpath = 'var/lib/freedombox/shares/'

    return path.split(subpath)[0]


def _get_shares() -> list[dict[str, str]]:
    """Get shares."""
    shares = []
    output = subprocess.check_output(['net', 'conf', 'list'])
    config = configparser.RawConfigParser()
    config.read_string(output.decode())
    for name in config.sections():
        share_type = 'open'
        if name.endswith('_group'):
            share_type = 'group'
        elif name.endswith('_home'):
            share_type = 'home'
        share_path = config[name]['path']
        mount_point = _get_mount_point(share_path)
        mount_point = os.path.normpath(mount_point)
        shares.append(
            dict(name=name, mount_point=mount_point, path=share_path,
                 share_type=share_type))

    return shares


def _get_shares_path(mount_point):
    """Return base path of the shared directories."""
    if mount_point == '/var':
        return 'lib/freedombox/shares/'
    var_directory = os.path.join(mount_point, 'var')

    if os.path.exists(var_directory) and os.stat(
            mount_point).st_dev == os.stat(var_directory).st_dev:
        return 'var/lib/freedombox/shares/'

    return 'FreedomBox/shares/'


def _set_open_share_permissions(directory):
    """Set file and directory permissions for open share."""
    shutil.chown(directory, group='freedombox-share')
    os.chmod(directory, 0o2775)
    for root, dirs, files in os.walk(directory):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            shutil.chown(subdir_path, group='freedombox-share')
            os.chmod(subdir_path, 0o2775)
        for file in files:
            file_path = os.path.join(root, file)
            shutil.chown(file_path, group='freedombox-share')
            os.chmod(file_path, 0o0664)
    subprocess.check_call(['setfacl', '-Rm', 'g::rwX', directory])
    subprocess.check_call(['setfacl', '-Rdm', 'g::rwX', directory])


def _use_config_file(conf_file):
    """Set samba configuration file location."""
    import augeas
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DEFAULT_FILE)
    aug.load()

    aug.set('/files' + DEFAULT_FILE + '/SMBDOPTIONS',
            '--configfile={0}'.format(conf_file))
    aug.save()


def _set_share_permissions(directory):
    """Set file and directory permissions for a share."""
    shutil.chown(directory, group='freedombox-share')
    os.chmod(directory, 0o2775)
    for root, dirs, files in os.walk(directory):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            shutil.chown(subdir_path, group='freedombox-share')
            os.chmod(subdir_path, 0o2775)
        for file in files:
            file_path = os.path.join(root, file)
            shutil.chown(file_path, group='freedombox-share')
            os.chmod(file_path, 0o0664)
    subprocess.check_call(['setfacl', '-Rm', 'g::rwX', directory])
    subprocess.check_call(['setfacl', '-Rdm', 'g::rwX', directory])


@privileged
def add_share(mount_point: str, share_type: str, windows_filesystem: bool):
    """Create a samba share."""
    if share_type not in ('open', 'group', 'home'):
        raise ValueError('Invalid share type')

    mount_point = os.path.normpath(mount_point)
    if not os.path.ismount(mount_point):
        raise RuntimeError(
            'Path "{0}" is not a mount point.'.format(mount_point))
    _create_share(mount_point, share_type, windows_filesystem)


@privileged
def delete_share(mount_point: str, share_type: str):
    """Delete a samba share configuration."""
    if share_type not in ('open', 'group', 'home'):
        raise ValueError('Invalid share type')

    mount_point = os.path.normpath(mount_point)
    shares = _get_shares()
    for share in shares:
        if share['mount_point'] == mount_point and share[
                'share_type'] == share_type:
            _close_share(share['name'])
            _conf_command(['delshare', share['name']])


@privileged
def get_shares() -> list[dict[str, str]]:
    """Get samba shares."""
    return _get_shares()


@privileged
def get_users() -> list[str]:
    """Get users from Samba database."""
    output = subprocess.check_output(['pdbedit', '-L']).decode()
    samba_users = [line.split(':')[0] for line in output.split()]
    return samba_users


@privileged
def setup():
    """Configure samba, use custom samba config file."""
    from plinth import action_utils
    with open(CONF_PATH, 'w', encoding='utf-8') as file_handle:
        file_handle.write(CONF)
    _use_config_file(CONF_PATH)
    os.makedirs('/var/lib/freedombox', exist_ok=True)
    os.chmod('/var/lib/freedombox', 0o0755)
    if action_utils.service_is_running('smbd'):
        action_utils.service_restart('smbd')


@privileged
def dump_shares():
    """Dump registy share configuration."""
    os.makedirs(os.path.dirname(SHARES_CONF_BACKUP_FILE), exist_ok=True)
    with open(SHARES_CONF_BACKUP_FILE, 'w', encoding='utf-8') as backup_file:
        command = ['net', 'conf', 'list']
        subprocess.run(command, stdout=backup_file, check=True)


@privileged
def restore_shares():
    """Restore registy share configuration."""
    if not os.path.exists(SHARES_CONF_BACKUP_FILE):
        raise RuntimeError(
            'Backup file {0} does not exist.'.format(SHARES_CONF_BACKUP_FILE))
    _conf_command(['drop'])
    _conf_command(['import', SHARES_CONF_BACKUP_FILE])
