# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities for regular updates and dist-upgrades."""

import pathlib
import re
import subprocess

import augeas

from plinth.modules.apache.components import check_url

RELEASE_FILE_URL = \
    'https://deb.debian.org/debian/dists/{}/Release'

DIST_UPGRADE_REQUIRED_FREE_SPACE = 5000000

sources_list = pathlib.Path('/etc/apt/sources.list')


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


def get_sources_list_codename() -> str | None:
    """Return the codename set in the /etc/apt/sources.list file."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('aptsources', str(sources_list))
    aug.set('/augeas/context', '/files' + str(sources_list))
    aug.load()

    dists = set()
    for match_ in aug.match('*'):
        dist = aug.get(match_ + '/distribution')
        if not dist:
            continue

        dist = dist.removesuffix('-updates')
        dist = dist.removesuffix('-security')
        dists.add(dist)

    if 'unstable' in dists or 'sid' in dists:
        return 'unstable'

    if 'testing' in dists:
        return 'testing'

    # Multiple distributions are not understood.
    if len(dists) != 1:
        return None

    return dists.pop()


def get_current_release():
    """Return current release and codename as a tuple."""
    output = subprocess.check_output(
        ['lsb_release', '--release', '--codename',
         '--short']).decode().strip()
    lines = output.split('\n')
    return lines[0], lines[1]


def is_distribution_unstable() -> bool:
    """Return whether the current distribution is unstable.

    There is no way to distinguish between 'testing' and 'unstable'
    distributions in Debian using commands like lsb_release (powered by
    /etc/os-release). See: https://lwn.net/Articles/984635/ . So, use the value
    set in /etc/apt/sources.list.
    """
    codename = get_sources_list_codename()
    return codename in ['unstable', 'sid']


def is_distribution_rolling() -> bool:
    """Return whether the current distribution is testing or unstable."""
    # Release will be 'n/a' in latest unstable and testing distributions.
    release, _ = get_current_release()
    return release in ['unstable', 'testing', 'n/a']
