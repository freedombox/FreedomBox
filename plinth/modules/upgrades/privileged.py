# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure or run unattended-upgrades."""

import logging
import os
import pathlib
import re
import subprocess

from plinth.action_utils import (apt_hold_flag, apt_unhold_freedombox,
                                 is_package_manager_busy, run_apt_command,
                                 service_is_running)
from plinth.actions import privileged

from . import distupgrade, utils

logger = logging.getLogger(__name__)

BACKPORTS_SOURCES_LIST = '/etc/apt/sources.list.d/freedombox2.list'

AUTO_CONF_FILE = '/etc/apt/apt.conf.d/20auto-upgrades'
LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades.log'
DPKG_LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades-dpkg.log'

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


def _release_held_freedombox():
    """If freedombox package was left in held state, release it.

    This can happen due to an interrupted process.
    """
    if apt_hold_flag.exists() and not is_package_manager_busy():
        apt_unhold_freedombox()


@privileged
def release_held_packages():
    """Release any packages that are being held."""
    if is_package_manager_busy():
        logger.warning('Package manager is busy, skipping releasing holds.')
        return

    if service_is_running('freedombox-dist-upgrade'):
        logger.warning('Distribution upgrade in progress, skipping releasing '
                       'holds.')
        return

    output = subprocess.check_output(['apt-mark', 'showhold']).decode().strip()
    holds = output.split('\n')
    logger.info('Releasing package holds: %s', holds)
    subprocess.run(['apt-mark', 'unhold', *holds], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)


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


@privileged
def check_auto() -> bool:
    """Check if automatic upgrades are enabled."""
    return utils.check_auto()


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
    if release in ['unstable', 'testing', 'n/a'] and not develop:
        logging.info(f'System release is {release}. Skip enabling backports.')
        return

    protocol = utils.get_http_protocol()
    if protocol == 'tor+http':
        logging.info('Package download over Tor is enabled.')

    if not utils.is_release_file_available(protocol, dist, backports=True):
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


@privileged
def start_dist_upgrade(test: bool = False):
    """Start dist upgrade process.

    Check if a new stable release is available, and start dist-upgrade process
    if updates are enabled.
    """
    _release_held_freedombox()

    distupgrade.start_service(test)


@privileged
def dist_upgrade():
    """Perform major distribution upgrade."""
    distupgrade.perform()


@privileged
def dist_upgrade_on_complete():
    """Perform cleanup operations after distribution upgrade."""
    distupgrade.on_complete()
