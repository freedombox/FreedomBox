# SPDX-License-Identifier: AGPL-3.0-or-later
"""Perform distribution upgrade."""

import contextlib
import logging
import pathlib
import subprocess
import time
from typing import Generator

from plinth.action_utils import (apt_hold, apt_hold_freedombox,
                                 debconf_set_selections, run_apt_command,
                                 service_daemon_reload, service_is_running,
                                 service_restart, service_start, service_stop)
from plinth.modules import snapshot as snapshot_module

from . import utils

SOURCES_LIST = '/etc/apt/sources.list'

DIST_UPGRADE_OBSOLETE_PACKAGES: list[str] = []

DIST_UPGRADE_PACKAGES_WITH_PROMPTS = [
    'bind9', 'firewalld', 'janus', 'minetest-server', 'minidlna',
    'mumble-server', 'radicale', 'roundcube-core', 'tt-rss'
]

DIST_UPGRADE_PRE_DEBCONF_SELECTIONS: list[str] = [
    # Tell grub-pc to continue without installing grub again.
    'grub-pc grub-pc/install_devices_empty boolean true'
]

DIST_UPGRADE_SERVICE = '''
[Unit]
Description=Upgrade to new stable Debian release

[Service]
Type=oneshot
ExecStart=systemd-inhibit /usr/share/plinth/actions/actions \
    upgrades dist_upgrade --no-args
KillMode=process
TimeoutSec=12hr
'''

DIST_UPGRADE_SERVICE_PATH = \
    '/run/systemd/system/freedombox-dist-upgrade.service'

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


def perform():
    """Perform upgrade to next release of Debian."""
    # If quassel is running during dist upgrade, it may be restarted
    # several times. This causes IRC users to rapidly leave/join
    # channels. Stop quassel for the duration of the dist upgrade.
    quassel_service = 'quasselcore'
    quassel_was_running = service_is_running(quassel_service)
    if quassel_was_running:
        print('Stopping quassel service before dist upgrade...', flush=True)
        service_stop(quassel_service)

    # Hold freedombox package during entire dist upgrade.
    print('Holding freedombox package...', flush=True)
    with apt_hold_freedombox(), _snapshot_run_and_disable():
        print('Updating Apt cache...', flush=True)
        run_apt_command(['update'])

        # Pre-set debconf selections if they are required during the
        # dist upgrade.
        if DIST_UPGRADE_PRE_DEBCONF_SELECTIONS:
            print(
                f'Setting debconf selections: '
                f'{DIST_UPGRADE_PRE_DEBCONF_SELECTIONS}', flush=True)
            debconf_set_selections(DIST_UPGRADE_PRE_DEBCONF_SELECTIONS)

        # Remove obsolete packages that may prevent other packages from
        # upgrading.
        if DIST_UPGRADE_OBSOLETE_PACKAGES:
            print(f'Removing packages: {DIST_UPGRADE_OBSOLETE_PACKAGES}...',
                  flush=True)
            run_apt_command(['remove'] + DIST_UPGRADE_OBSOLETE_PACKAGES)

        # Hold packages known to have conffile prompts. FreedomBox service
        # will handle their upgrade later.
        print(
            'Holding packages with conffile prompts: ' +
            ', '.join(DIST_UPGRADE_PACKAGES_WITH_PROMPTS) + '...', flush=True)
        with apt_hold(DIST_UPGRADE_PACKAGES_WITH_PROMPTS):
            print('Running apt full-upgrade...', flush=True)
            returncode = run_apt_command(['full-upgrade'])

        # Check if apt upgrade was successful.
        if returncode:
            raise RuntimeError(
                'Apt full-upgrade was not successful. Distribution upgrade '
                'will be retried at a later time.')

        if quassel_was_running:
            print('Re-starting quassel service after dist upgrade...',
                  flush=True)
            service_start(quassel_service)

        print('Running apt autoremove...', flush=True)
        run_apt_command(['autoremove'])

    # Run unattended-upgrade once more to handle upgrading the
    # freedombox package.
    print('Running unattended-upgrade...', flush=True)
    subprocess.run(['unattended-upgrade', '--verbose'], check=False)

    # Restart FreedomBox service to ensure it is using the latest
    # dependencies.
    print('Restarting FreedomBox service...', flush=True)
    service_restart('plinth')

    # After 10 minutes, update apt cache again to trigger force_upgrades.
    print('Waiting for 10 minutes...', flush=True)
    time.sleep(10 * 60)
    print('Updating Apt cache...', flush=True)
    run_apt_command(['update'])

    print('Dist upgrade complete. Removing flag.', flush=True)
    if dist_upgrade_flag.exists():
        dist_upgrade_flag.unlink()


def start_service():
    """Create dist upgrade service and start it."""
    with open(DIST_UPGRADE_SERVICE_PATH, 'w',
              encoding='utf-8') as service_file:
        service_file.write(DIST_UPGRADE_SERVICE)

    service_daemon_reload()
    subprocess.Popen(['systemctl', 'start', 'freedombox-dist-upgrade'],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     start_new_session=True)
