# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Minor utility methods for Cockpit.
"""

import urllib.parse

import augeas

CONFIG_FILE = '/etc/cockpit/cockpit.conf'


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/inifile/lens', 'Puppet.lns')
    aug.set('/augeas/load/inifile/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug


def get_origin_domains(aug):
    """Return the list of allowed origin domains."""
    origins = aug.get('/files' + CONFIG_FILE + '/WebService/Origins')
    return set(origins.split()) if origins else set()


def get_origin_from_domain(domain):
    """Return the origin that should be allowed for a domain."""
    return 'https://{domain}'.format(domain=domain)


def _get_domain_from_origin(origin):
    """Return the domain from an origin URL."""
    return urllib.parse.urlparse(origin).netloc


def get_domains():
    """Return the domain name in origin URL."""
    aug = load_augeas()
    origins = get_origin_domains(aug)
    return [_get_domain_from_origin(origin) for origin in origins]
