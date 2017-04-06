#
# This file is part of Plinth.
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
Plinth module to configure name services
"""

from django.utils.translation import ugettext_lazy as _
import logging

from plinth.menu import main_menu
from plinth.signals import domain_added, domain_removed


SERVICES = (
    ('http', _('HTTP'), 80),
    ('https', _('HTTPS'), 443),
    ('ssh', _('SSH'), 22),
)

version = 1

is_essential = True

title = _('Name Services')

domain_types = {}
domains = {}

logger = logging.getLogger(__name__)


def init():
    """Initialize the names module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-tag', 'names:index')

    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)


def on_domain_added(sender, domain_type, name='', description='',
                    services=None, **kwargs):
    """Add domain to global list."""
    if not domain_type:
        return

    domain_types[domain_type] = description

    if not name:
        return
    if not services:
        services = []

    if domain_type not in domains:
        # new domain_type
        domains[domain_type] = {}
    domains[domain_type][name] = services
    logger.info('Added domain %s of type %s with services %s',
                name, domain_type, str(services))


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    if domain_type in domains:
        if name == '':  # remove all domains of this type
            domains[domain_type] = {}
            logger.info('Removed all domains of type %s', domain_type)
        elif name in domains[domain_type]:
            del domains[domain_type][name]
            logger.info('Removed domain %s of type %s', name, domain_type)


def get_domain_types():
    """Get list of domain_types."""
    return list(domain_types.keys())


def get_description(domain_type):
    """Get description of a domain_type, if available."""
    if domain_type in domain_types:
        return domain_types[domain_type]
    else:
        return domain_type


def get_domain(domain_type):
    """
    Get domain of type domain_type.

    This function is meant for use with single-domain domain_types. If there is
    more than one domain, any one of the domains may be returned.
    """
    if domain_type in domains and len(domains[domain_type]) > 0:
        return list(domains[domain_type].keys())[0]
    else:
        return None


def get_enabled_services(domain_type, domain):
    """Get list of enabled services for a domain."""
    try:
        return domains[domain_type][domain]
    except KeyError:
        # domain_type or domain not registered
        return []


def get_services_status(domain_type, domain):
    """Get list of whether each service is enabled for a domain."""
    enabled = get_enabled_services(domain_type, domain)
    return [service[0] in enabled for service in SERVICES]
