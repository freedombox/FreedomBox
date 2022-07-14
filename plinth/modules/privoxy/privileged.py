# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure privoxy."""

import pathlib

import augeas

from plinth import action_utils
from plinth.actions import privileged

PRIVOXY_CONF_PATH = pathlib.Path('/etc/privoxy/config')


@privileged
def pre_install():
    """Preseed debconf values before packages are installed."""
    action_utils.debconf_set_selections(
        ['privoxy privoxy/listen-address string [::]:8118'])


@privileged
def setup():
    """Setup Privoxy configuration after installing it."""
    _restrict_access()


def _load_augeus():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Spacevars', str(PRIVOXY_CONF_PATH))
    aug.set('/augeas/context', '/files' + str(PRIVOXY_CONF_PATH))
    aug.load()
    return aug


def _restrict_access():
    """Make sure Privoxy isn't available over the Internet."""
    # https://en.wikipedia.org/wiki/localhost
    # https://en.wikipedia.org/wiki/Private_network
    # https://en.wikipedia.org/wiki/Link-local_address
    # https://en.wikipedia.org/wiki/Unique_local_address
    ip_ranges = [
        '127.0.0.0/8',  # IPv4 loopback address
        '10.0.0.0/8',  # IPv4 private address
        '172.16.0.0/12',  # IPv4 private address
        '192.168.0.0/16',  # IPv4 private address
        '169.254.0.0/16',  # IPv4 auto-configuration
        '[::1]',  # IPv4 loopback address
        '[fc00::]/7',  # IPv6 unique local addresses
        '[fe80::]/10',  # IPv6 auto-configuration
    ]
    aug = _load_augeus()
    for ip_range in ip_ranges:
        matches = [
            match for match in aug.match('permit-access')
            if aug.get(match) == ip_range
        ]
        if not any(matches):
            aug.set('permit-access[last() + 1]', ip_range)

    aug.save()
