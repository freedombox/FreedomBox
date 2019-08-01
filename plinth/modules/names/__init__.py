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
FreedomBox app to configure name services.
"""

import logging

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import components
from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

name = _('Name Services')

logger = logging.getLogger(__name__)

manual_page = 'NameServices'

description = [
    format_lazy(
        _('Name Services provides an overview of the ways {box_name} can be '
          'reached from the public Internet: domain name, Tor hidden service, '
          'and Pagekite. For each type of name, it is shown whether the HTTP, '
          'HTTPS, and SSH services are enabled or disabled for incoming '
          'connections through the given name.'), box_name=(cfg.box_name))
]

app = None


class NamesApp(app_module.App):
    """FreedomBox app for names."""

    app_id = 'names'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-names', name, None, 'fa-tags',
                              'names:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the names module."""
    global app
    app = NamesApp()
    app.set_enabled(True)

    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)


def on_domain_added(sender, domain_type, name='', description='',
                    services=None, **kwargs):
    """Add domain to global list."""
    if not domain_type:
        return

    if not name:
        return
    if not services:
        services = []

    components.DomainName('domain-' + sender + '-' + name, name, domain_type,
                          services)
    logger.info('Added domain %s of type %s with services %s', name,
                domain_type, str(services))


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    if name:
        component_id = 'domain-' + sender + '-' + name
        components.DomainName.get(component_id).remove()
        logger.info('Removed domain %s of type %s', name, domain_type)
    else:
        for domain_name in components.DomainName.list():
            if domain_name.domain_type.component_id == domain_type:
                domain_name.remove()

                logger.info('Remove domain %s of type %s', domain_name.name,
                            domain_type)
