# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure or run unattended-upgrades."""

import logging
import os
import pathlib
import re
import subprocess
import time

from plinth.action_utils import (apt_hold, apt_hold_flag, apt_hold_freedombox,
                                 apt_unhold_freedombox, debconf_set_selections,
                                 is_package_manager_busy, run_apt_command,
                                 service_daemon_reload, service_is_running,
                                 service_restart, service_start, service_stop)
from plinth.actions import privileged
from plinth.modules.apache.components import check_url
from plinth.modules.snapshot import is_apt_snapshots_enabled
from plinth.modules.snapshot import is_supported as snapshot_is_supported
from plinth.modules.snapshot import load_augeas as snapshot_load_augeas

SOURCES_LIST = '/etc/apt/sources.list'
BACKPORTS_SOURCES_LIST = '/etc/apt/sources.list.d/freedombox2.list'

AUTO_CONF_FILE = '/etc/apt/apt.conf.d/20auto-upgrades'
LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades.log'
DPKG_LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades-dpkg.log'
RELEASE_FILE_URL = \
    'https://deb.debian.org/debian/dists/{}/Release'

APT_PREFERENCES_FREEDOMBOX = \
    '''Explanation: This file is managed by FreedomBox, do not edit.
Explanation: Allow carefully selected updates to 'freedombox' from backports.
Package: src:freedombox
Pin: release n={}-backports
Pin-Priority: 500
'''

# Whenever these preferences needs to change, increment the version number
# upgrades app. This ensures that setup is run again and the new contents are
# overwritten on the old file.
APT_PREFERENCES_APPS = \
    '''Explanation: This file is managed by FreedomBox, do not edit.
Explanation: matrix-synapse shall not be available in Debian stable but
Explanation: only in backports. Upgrade priority of packages that have needed
Explanation: versions only in backports.
Explanation: matrix-synapse >= 1.92.0-3 requires
Explanation: python3-canonicaljson >= 2.0.0~
Package: python3-canonicaljson
Pin: release n=bookworm-backports
Pin-Priority: 500
'''

DIST_UPGRADE_OBSOLETE_PACKAGES: list[str] = []

DIST_UPGRADE_PACKAGES_WITH_PROMPTS = [
    'bind9', 'firewalld', 'janus', 'minetest-server', 'minidlna',
    'mumble-server', 'radicale', 'roundcube-core', 'tt-rss'
]

DIST_UPGRADE_PRE_INSTALL_PACKAGES = ['base-files']

DIST_UPGRADE_PRE_DEBCONF_SELECTIONS: list[str] = [
    # Tell grub-pc to continue without installing grub again.
    'grub-pc grub-pc/install_devices_empty boolean true'
]

DIST_UPGRADE_REQUIRED_FREE_SPACE = 5000000

DIST_UPGRADE_SERVICE = '''
[Unit]
Description=Upgrade to new stable Debian release

[Service]
Type=oneshot
ExecStart=/usr/share/plinth/actions/actions upgrades dist_upgrade --no-args
KillMode=process
TimeoutSec=12hr
'''

DIST_UPGRADE_SERVICE_PATH = \
    '/run/systemd/system/freedombox-dist-upgrade.service'

dist_upgrade_flag = pathlib.Path(
    '/var/lib/freedombox/dist-upgrade-in-progress')


def _release_held_freedombox():
    """If freedombox package was left in held state, release it.

    This can happen due to an interrupted process.
    """
    if apt_hold_flag.exists() and not is_package_manager_busy():
        apt_unhold_freedombox()


@privileged
def run():
    """Run unattended-upgrades."""
    subprocess.run(['dpkg', '--configure', '-a'], check=False)
    run_apt_command(['--fix-broken', 'install'])
    _release_held_freedombox()

    subprocess.Popen(['systemctl', 'start', 'freedombox-manual-upgrade'],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     start_new_session=True)


def _check_auto() -> bool:
    """Check if automatic upgrades are enabled."""
    arguments = [
        'apt-config', 'shell', 'UpdateInterval',
        'APT::Periodic::Update-Package-Lists'
    ]
    output = subprocess.check_output(arguments).decode()
    update_interval = 0
    match = re.match(r"UpdateInterval='(.*)'", output)
    if match:
        update_interval = int(match.group(1))

    return bool(update_interval)


@privileged
def check_auto() -> bool:
    """Check if automatic upgrades are enabled."""
    return _check_auto()


@privileged
def enable_auto():
    """Enable automatic upgrades."""
    with open(AUTO_CONF_FILE, 'w', encoding='utf-8') as conffile:
        conffile.write('APT::Periodic::Update-Package-Lists "1";\n')
        conffile.write('APT::Periodic::Unattended-Upgrade "1";\n')


@privileged
def disable_auto():
    """Disable automatic upgrades."""
    with open(AUTO_CONF_FILE, 'w', encoding='utf-8') as conffile:
        conffile.write('APT::Periodic::Update-Package-Lists "0";\n')
        conffile.write('APT::Periodic::Unattended-Upgrade "0";\n')


@privileged
def get_log() -> str:
    """Return the automatic upgrades log."""
    log_lines = []
    try:
        log_lines.append('==> ' + os.path.basename(LOG_FILE))
        with open(LOG_FILE, 'r', encoding='utf-8') as file_handle:
            log_lines.append(file_handle.read())
    except IOError:
        pass

    try:
        log_lines.append('==> ' + os.path.basename(DPKG_LOG_FILE))
        with open(DPKG_LOG_FILE, 'r', encoding='utf-8') as file_handle:
            log_lines.append(file_handle.read())
    except IOError:
        pass

    return '\n'.join(log_lines)


def _get_protocol() -> str:
    """Return the protocol to use for newly added repository sources."""
    try:
        from plinth.modules.torproxy import utils
        if utils.is_apt_transport_tor_enabled():
            return 'tor+http'
    except Exception:
        pass

    return 'http'


def _is_release_file_available(protocol: str, dist: str,
                               backports=False) -> bool:
    """Return whether the release for dist[-backports] is available."""
    wrapper = None
    if protocol == 'tor+http':
        wrapper = 'torsocks'

    if backports:
        dist += '-backports'

    try:
        return check_url(RELEASE_FILE_URL.format(dist), wrapper=wrapper)
    except FileNotFoundError:
        return False


def _add_backports_sources(sources_list: str, protocol: str, dist: str):
    """Add backports sources to freedombox repositories list."""
    sources = '''# This file is managed by FreedomBox, do not edit.
# Allow carefully selected updates to 'freedombox' from backports.

deb {protocol}://deb.debian.org/debian {dist}-backports main
deb-src {protocol}://deb.debian.org/debian {dist}-backports main
'''
    sources = sources.format(protocol=protocol, dist=dist)
    with open(sources_list, 'w', encoding='utf-8') as file_handle:
        file_handle.write(sources)


def _check_and_backports_sources(develop=False):
    """Add backports sources after checking if it is available."""
    old_sources_list = '/etc/apt/sources.list.d/freedombox.list'
    if os.path.exists(old_sources_list):
        os.remove(old_sources_list)

    from plinth.modules.upgrades import (get_current_release,
                                         is_backports_current)
    if is_backports_current():
        logging.info('Repositories list up-to-date. Skipping update.')
        return

    try:
        with open('/etc/dpkg/origins/default', 'r',
                  encoding='utf-8') as default_origin:
            matches = [
                re.match(r'Vendor:\s+(Debian|FreedomBox)', line,
                         flags=re.IGNORECASE)
                for line in default_origin.readlines()
            ]
    except FileNotFoundError:
        logging.info('Could not open /etc/dpkg/origins/default')
        return

    if not any(matches):
        logging.info('System is running a derivative of Debian. Skip enabling '
                     'backports.')
        return

    release, dist = get_current_release()
    if release == 'unstable' or (release == 'testing' and not develop):
        logging.info(f'System release is {release}. Skip enabling backports.')
        return

    protocol = _get_protocol()
    if protocol == 'tor+http':
        logging.info('Package download over Tor is enabled.')

    if not _is_release_file_available(protocol, dist, backports=True):
        logging.info(
            f'Release file for {dist}-backports is not available yet.')
        return

    print(f'{dist}-backports is now available. Adding to sources.')
    _add_backports_sources(BACKPORTS_SOURCES_LIST, protocol, dist)
    # In case of dist upgrade, rewrite the preferences file.
    _add_apt_preferences()


def _add_apt_preferences():
    """Setup APT preferences to upgrade selected packages from backports."""
    base_path = pathlib.Path('/etc/apt/preferences.d')
    for file_name in ['50freedombox.pref', '50freedombox2.pref']:
        full_path = base_path / file_name
        if full_path.exists():
            full_path.unlink()

    # Don't try to remove 50freedombox3.pref as this file is shipped with the
    # Debian package and is removed using maintainer scripts.

    from plinth.modules.upgrades import get_current_release
    _, dist = get_current_release()
    if dist == 'sid':
        logging.info(
            f'System distribution is {dist}. Skip setting apt preferences '
            'for backports.')
    else:
        logging.info(f'Setting apt preferences for {dist}-backports.')
        with open(base_path / '50freedombox4.pref', 'w',
                  encoding='utf-8') as file_handle:
            file_handle.write(APT_PREFERENCES_FREEDOMBOX.format(dist))
        with open(base_path / '51freedombox-apps.pref', 'w',
                  encoding='utf-8') as file_handle:
            file_handle.write(APT_PREFERENCES_APPS)


def _is_sufficient_free_space() -> bool:
    """Return whether there is sufficient free space for dist upgrade."""
    output = subprocess.check_output(['df', '--output=avail', '/'])
    free_space = int(output.decode().split('\n')[1])
    return free_space >= DIST_UPGRADE_REQUIRED_FREE_SPACE


def _check_dist_upgrade(test_upgrade=False) -> tuple[bool, str]:
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
    if release in ['unstable', 'testing']:
        return (False, f'already-{release}')

    check_dists = ['stable']
    if test_upgrade:
        check_dists.append('testing')

    codename = None
    for check_dist in check_dists:
        url = RELEASE_FILE_URL.format(check_dist)
        command = ['curl', '--silent', '--location', '--fail', url]
        protocol = _get_protocol()
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

    if not _check_auto():
        return (False, 'upgrades-not-enabled')

    if check_dist == 'testing' and not test_upgrade:
        return (False, 'test-not-set')

    if not _is_sufficient_free_space():
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


def _take_snapshot_and_disable() -> bool:
    """Take a snapshot if supported and enabled, then disable snapshots.

    Return whether snapshots shall be re-enabled at the end.
    """
    if snapshot_is_supported():
        print('Taking a snapshot before dist upgrade...', flush=True)
        subprocess.run([
            '/usr/share/plinth/actions/actions', 'snapshot', 'create',
            '--no-args'
        ], check=True)
        aug = snapshot_load_augeas()
        if is_apt_snapshots_enabled(aug):
            print('Disable apt snapshots during dist upgrade...', flush=True)
            subprocess.run([
                '/usr/share/plinth/actions/actions',
                'snapshot',
                'disable_apt_snapshot',
            ], input='{"args": ["yes"], "kwargs": {}}'.encode(), check=True)
            return True
        else:
            print('Apt snapshots already disabled.', flush=True)
    else:
        print('Snapshots are not supported, skip taking a snapshot.',
              flush=True)

    return False


def _restore_snapshots_config(reenable=False):
    """Restore original snapshots configuration."""
    if reenable:
        print('Re-enable apt snapshots...', flush=True)
        subprocess.run([
            '/usr/share/plinth/actions/actions', 'snapshot',
            'disable_apt_snapshot'
        ], input='{"args": ["no"], "kwargs": {}}'.encode(), check=True)


def _disable_searx() -> bool:
    """If searx is enabled, disable it until we can upgrade it properly.

    Return whether searx was originally enabled.
    """
    searx_is_enabled = pathlib.Path(
        '/etc/uwsgi/apps-enabled/searx.ini').exists()
    if searx_is_enabled:
        print('Disabling searx...', flush=True)
        subprocess.run(
            ['/usr/share/plinth/actions/actions', 'apache', 'uwsgi_disable'],
            input='{"args": ["searx"], "kwargs": {}}'.encode(), check=True)

    return searx_is_enabled


def _update_searx(reenable=False):
    """If searx is installed, update search engines list.

    Re-enable if previously enabled.
    """
    if pathlib.Path('/etc/searx/settings.yml').exists():
        print('Updating searx search engines list...', flush=True)
        subprocess.run([
            '/usr/share/plinth/actions/actions', 'searx', 'setup', '--no-args'
        ], check=True)
        if reenable:
            print('Re-enabling searx after upgrade...', flush=True)
            subprocess.run([
                '/usr/share/plinth/actions/actions', 'apache', 'uwsgi_enable'
            ], input='{"args": ["searx"], "kwargs": {}}'.encode(), check=True)


def _perform_dist_upgrade():
    """Perform upgrade to next release of Debian."""
    reenable_snapshots = _take_snapshot_and_disable()
    reenable_searx = _disable_searx()

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
    with apt_hold_freedombox():
        print('Updating Apt cache...', flush=True)
        run_apt_command(['update'])

        # Install packages that are necessary for unattended-upgrades
        # to start the dist upgrade.
        print(f'Upgrading packages: {DIST_UPGRADE_PRE_INSTALL_PACKAGES}...',
              flush=True)
        run_apt_command(['install'] + DIST_UPGRADE_PRE_INSTALL_PACKAGES)

        # Pre-set debconf selections if they are required during the
        # dist upgrade.
        if DIST_UPGRADE_PRE_DEBCONF_SELECTIONS:
            print(
                f'Setting debconf selections: '
                f'{DIST_UPGRADE_PRE_DEBCONF_SELECTIONS}', flush=True)
            debconf_set_selections(DIST_UPGRADE_PRE_DEBCONF_SELECTIONS)

        # This will upgrade most of the packages.
        # Previously, when dist-upgrading from bullseye to bookworm, there was
        # an issue where unattended-upgrade gets stuck. See #2266.  However, it
        # does not get stuck when dist-upgrading from bookworm to trixie.
        print('Running unattended-upgrade...', flush=True)
        subprocess.run(['unattended-upgrade', '--verbose'], check=False)

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

        _update_searx(reenable_searx)

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

    _restore_snapshots_config(reenable_snapshots)

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


@privileged
def setup():
    """Setup apt preferences."""
    _add_apt_preferences()


@privileged
def activate_backports(develop: bool = False):
    """Setup software repositories needed for FreedomBox.

    Repositories list for now only contains the backports. If the file exists,
    assume that it contains backports.
    """
    _check_and_backports_sources(develop)


def _start_dist_upgrade_service():
    """Create dist upgrade service and start it."""
    with open(DIST_UPGRADE_SERVICE_PATH, 'w',
              encoding='utf-8') as service_file:
        service_file.write(DIST_UPGRADE_SERVICE)

    service_daemon_reload()
    subprocess.Popen(['systemctl', 'start', 'freedombox-dist-upgrade'],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     start_new_session=True)


@privileged
def start_dist_upgrade(test: bool = False) -> dict[str, str | bool]:
    """Start dist upgrade process.

    Check if a new stable release is available, and start dist-upgrade process
    if updates are enabled.
    """
    _release_held_freedombox()

    upgrade_ready, reason = _check_dist_upgrade(test)
    if upgrade_ready:
        _start_dist_upgrade_service()

    return {'dist_upgrade_started': upgrade_ready, 'reason': reason}


@privileged
def dist_upgrade():
    """Perform major distribution upgrade."""
    _perform_dist_upgrade()
