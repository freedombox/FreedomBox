# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities for regular updates and dist-upgrades."""

import re
import subprocess

from plinth.modules.apache.components import check_url

RELEASE_FILE_URL = \
    'https://deb.debian.org/debian/dists/{}/Release'

DIST_UPGRADE_REQUIRED_FREE_SPACE = 5000000


def check_auto() -> bool:
    """Return whether automatic updates are enabled."""
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


def get_http_protocol() -> str:
    """Return the protocol to use for newly added repository sources."""
    try:
        from plinth.modules.torproxy import utils
        if utils.is_apt_transport_tor_enabled():
            return 'tor+http'
    except Exception:
        pass

    return 'http'


def is_release_file_available(protocol: str, dist: str,
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


def is_sufficient_free_space() -> bool:
    """Return whether there is sufficient free space for dist upgrade."""
    output = subprocess.check_output(['df', '--output=avail', '/'])
    free_space = int(output.decode().split('\n')[1])
    return free_space >= DIST_UPGRADE_REQUIRED_FREE_SPACE
