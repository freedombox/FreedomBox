#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
