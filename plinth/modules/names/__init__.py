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

from gettext import gettext as _
import logging

from plinth import cfg
from plinth.signals import domain_added, domain_removed


depends = ['plinth.modules.system',
           'plinth.modules.firewall']

domain_types = {}
domains = {}

logger = logging.getLogger(__name__)


def init():
    """Initialize the names module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Name Services'), 'glyphicon-th', 'names:index', 19)

    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)


def on_domain_added(sender, domain_type, name, description, **kwargs):
    """Add domain to global list."""
    global domain_types, domains
    domain_types[domain_type] = description
    if domain_type in domains and name and name not in domains[domain_type]:
        domains[domain_type].append(name)
        logger.info('Added %s domain: %s', domain_type, name)
    elif name:  # not blank
        domains[domain_type] = [name]
        logger.info('Added %s domain: %s', domain_type, name)


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    global domains
    if domain_type in domains:
        if name == '':  # remove all domains of this type
            domains[domain_type] = []
            logger.info('Removed all %s domains', domain_type)
        elif name in domains[domain_type]:
            domains[domain_type].remove(name)
            logger.info('Removed %s domain: %s', domain_type, name)


def get_domain(domain_type):
    """Get the first domain of type domain_type."""
    global domains
    if domain_type in domains and len(domains[domain_type]) > 0:
        return domains[domain_type][0]
    else:
        return None
