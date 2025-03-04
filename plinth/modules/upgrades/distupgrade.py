# SPDX-License-Identifier: AGPL-3.0-or-later
"""Perform distribution upgrade."""

import contextlib
import logging
import pathlib
import subprocess
import time
from typing import Generator

from plinth import action_utils
from plinth.modules import snapshot as snapshot_module

from . import utils

SOURCES_LIST = '/etc/apt/sources.list'

DIST_UPGRADE_OBSOLETE_PACKAGES: list[str] = []

DIST_UPGRADE_PACKAGES_WITH_PROMPTS = ['firewalld', 'minidlna', 'radicale']

DIST_UPGRADE_PRE_DEBCONF_SELECTIONS: list[str] = [
    # Tell grub-pc to continue without installing grub again.
    'grub-pc grub-pc/install_devices_empty boolean true'
]

dist_upgrade_flag = pathlib.Path(
    '/var/lib/freedombox/dist-upgrade-in-progress')


def check(test_upgrade=False) -> tuple[bool, str]:
    """Check if a distribution upgrade be performed.

    Check for new stable release, if updates are enabled, and if there is
    enough free space for the dist upgrade.

    If test_upgrade is True, also check for upgrade to testing.

    Return (boolean, string) indicating if the upgrade is ready, and a reason
    if not.
    """
    if dist_upgrade_flag.exists():
        return (True, 'found-previous')

    from plinth.modules.upgrades import get_current_release
    release, dist = get_current_release()
    if release in ['unstable', 'testing', 'n/a']:
        return (False, f'already-{release}')

    check_dists = ['stable']
    if test_upgrade:
        check_dists.append('testing')

    codename = None
    for check_dist in check_dists:
        url = utils.RELEASE_FILE_URL.format(check_dist)
        command = ['curl', '--silent', '--location', '--fail', url]
        protocol = utils.get_http_protocol()
        if protocol == 'tor+http':
            command.insert(0, 'torsocks')
            logging.info('Package download over Tor is enabled.')

        try:
            output = subprocess.check_output(command).decode()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning('Error while checking for new %s release',
                            check_dist)
        else:
            for line in output.split('\n'):
                if line.startswith('Codename:'):
                    codename = line.split()[1]

    if not codename:
        return (False, 'codename-not-found')

    if codename == dist:
        return (False, f'already-{dist}')

    if not utils.check_auto():
        return (False, 'upgrades-not-enabled')

    if check_dist == 'testing' and not test_upgrade:
        return (False, 'test-not-set')

    if not utils.is_sufficient_free_space():
        return (False, 'not-enough-free-space')

    logging.info('Upgrading from %s to %s...', dist, codename)
    with open(SOURCES_LIST, 'r', encoding='utf-8') as sources_list:
        lines = sources_list.readlines()

    with open(SOURCES_LIST, 'w', encoding='utf-8') as sources_list:
        for line in lines:
            # E.g. replace 'bullseye' with 'bookworm'.
            new_line = line.replace(dist, codename)
            if check_dist == 'testing':
                # E.g. replace 'stable' with 'bookworm'.
                new_line = new_line.replace('stable', codename)

            sources_list.write(new_line)

    logging.info('Dist upgrade in progress. Setting flag.')
    dist_upgrade_flag.touch(mode=0o660)
    return (True, 'started-dist-upgrade')


@contextlib.contextmanager
def _snapshot_run_and_disable() -> Generator[None, None, None]:
    """Take a snapshot if supported and enabled, then disable snapshots.

    Snapshots shall be re-enabled, if originally enabled, on exiting this
    context manager..
    """
    if not snapshot_module.is_supported():
        print('Snapshots are not supported, skipping taking a snapshot.',
              flush=True)
        yield
        return

    reenable = False
    try:
        print('Taking a snapshot before dist upgrade...', flush=True)
        subprocess.run([
            '/usr/share/plinth/actions/actions', 'snapshot', 'create',
            '--no-args'
        ], check=True)
        aug = snapshot_module.load_augeas()
        if snapshot_module.is_apt_snapshots_enabled(aug):
            print('Disabling apt snapshots during dist upgrade...', flush=True)
            subprocess.run([
                '/usr/share/plinth/actions/actions',
                'snapshot',
                'disable_apt_snapshot',
            ], input='{"args": ["yes"], "kwargs": {}}'.encode(), check=True)
            reenable = True
        else:
            print('Apt snapshots already disabled.', flush=True)

        yield
    finally:
        if reenable:
            print('Re-enabling apt snapshots...', flush=True)
            subprocess.run([
                '/usr/share/plinth/actions/actions', 'snapshot',
                'disable_apt_snapshot'
            ], input='{"args": ["no"], "kwargs": {}}'.encode(), check=True)
        else:
            print('Not re-enabling apt snapshots, as they were disabled '
                  'before dist upgrade.')


@contextlib.contextmanager
def _services_disable():
    """Disable services that are seriously impacted by the upgrade."""
    # If quassel is running during dist upgrade, it may be restarted
    # several times. This causes IRC users to rapidly leave/join
    # channels. Stop quassel for the duration of the dist upgrade.
    print('Stopping quassel service during dist upgrade...', flush=True)
    with action_utils.service_ensure_stopped('quasselcore'):
        yield
        print('Re-enabling quassel service if previously enabled...',
              flush=True)


@contextlib.contextmanager
def _apt_hold_packages():
    """Apt hold some packages during dist upgrade."""
    packages = DIST_UPGRADE_PACKAGES_WITH_PROMPTS
    packages_string = ', '.join(packages)

    # Hold freedombox package during entire dist upgrade.
    print('Holding freedombox package...', flush=True)
    with action_utils.apt_hold_freedombox():
        # Hold packages known to have conffile prompts. FreedomBox service
        # will handle their upgrade later.
        print(f'Holding packages with conffile prompts: {packages_string}...',
              flush=True)
        with action_utils.apt_hold(packages):
            yield
            print(
                'Releasing holds on packages with conffile prompts: '
                f'{packages_string}...', flush=True)

        print('Releasing hold on freedombox package...')


def _debconf_set_selections() -> None:
    """Pre-set debconf selections if they are needed for dist upgrade."""
    if DIST_UPGRADE_PRE_DEBCONF_SELECTIONS:
        print(
            f'Setting debconf selections: '
            f'{DIST_UPGRADE_PRE_DEBCONF_SELECTIONS}', flush=True)
        action_utils.debconf_set_selections(
            DIST_UPGRADE_PRE_DEBCONF_SELECTIONS)


def _packages_remove_obsolete() -> None:
    """Remove obsolete packages.

    These may prevent other packages from upgrading.
    """
    if DIST_UPGRADE_OBSOLETE_PACKAGES:
        print(f'Removing packages: {DIST_UPGRADE_OBSOLETE_PACKAGES}...',
              flush=True)
        action_utils.run_apt_command(['remove'] +
                                     DIST_UPGRADE_OBSOLETE_PACKAGES)


def _apt_update():
    """Run 'apt update'."""
    print('Updating Apt cache...', flush=True)
    action_utils.run_apt_command(['update'])


def _apt_autoremove():
    """Run 'apt autoremove'."""
    print('Running apt autoremove...', flush=True)
    action_utils.run_apt_command(['autoremove'])


def _apt_full_upgrade():
    """Run and check if apt upgrade was successful."""
    print('Running apt full-upgrade...', flush=True)
    returncode = action_utils.run_apt_command(['full-upgrade'])
    if returncode:
        raise RuntimeError(
            'Apt full-upgrade was not successful. Distribution upgrade '
            'will be retried at a later time.')


def _unattended_upgrades_run():
    """Run unattended-upgrade once more.

    To handle upgrading the freedombox package.
    """
    print('Running unattended-upgrade...', flush=True)
    subprocess.run(['unattended-upgrade', '--verbose'], check=False)


def _freedombox_restart():
    """Restart FreedomBox service.

    To ensure it is using the latest dependencies.
    """
    print('Restarting FreedomBox service...', flush=True)
    action_utils.service_restart('plinth')


def _wait():
    """Wait for 10 minutes before performing remaining actions."""
    print('Waiting for 10 minutes...', flush=True)
    time.sleep(10 * 60)


def _flag_remove():
    """Remove the flag that mark that dist upgrade is running."""
    print('Dist upgrade complete. Removing flag.', flush=True)
    if dist_upgrade_flag.exists():
        dist_upgrade_flag.unlink()


def perform():
    """Perform upgrade to next release of Debian."""
    with _snapshot_run_and_disable(), \
         _services_disable(), \
         _apt_hold_packages():
        _apt_update()
        _debconf_set_selections()
        _packages_remove_obsolete()
        _apt_full_upgrade()
        _apt_autoremove()

    _unattended_upgrades_run()
    _freedombox_restart()
    _wait()
    _apt_update()
    _flag_remove()


def start_service():
    """Create dist upgrade service and start it."""
    old_service_path = pathlib.Path(
        '/run/systemd/system/freedombox-dist-upgrade.service')
    if old_service_path.exists():
        old_service_path.unlink(missing_ok=True)
        action_utils.service_daemon_reload()

    args = [
        '--unit=freedombox-dist-upgrade',
        '--description=Upgrade to new stable Debian release',
        '--property=KillMode=process',
        '--property=TimeoutSec=12hr',
    ]
    subprocess.run(['systemd-run'] + args + [
        'systemd-inhibit', '/usr/share/plinth/actions/actions', 'upgrades',
        'dist_upgrade', '--no-args'
    ], check=True)
