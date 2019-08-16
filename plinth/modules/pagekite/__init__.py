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
FreedomBox app to configure PageKite.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.modules.names.components import DomainType
from plinth.utils import format_lazy

from . import utils
from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

depends = ['names']

managed_services = ['pagekite']

managed_packages = ['pagekite']

first_boot_steps = [
    {
        'id': 'pagekite_firstboot',
        'url': 'pagekite:firstboot',
        'order': 5,
    },
]

name = _('PageKite')

short_description = _('Public Visibility')

description = [
    format_lazy(
        _('PageKite is a system for exposing {box_name} services when '
          'you don\'t have a direct connection to the Internet. You only '
          'need this if your {box_name} services are unreachable from '
          'the rest of the Internet. This includes the following '
          'situations:'), box_name=_(cfg.box_name)),
    format_lazy(
        _('{box_name} is behind a restricted firewall.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('{box_name} is connected to a (wireless) router which you '
          'don\'t control.'), box_name=_(cfg.box_name)),
    _('Your ISP does not provide you an external IP address and '
      'instead provides Internet connection through NAT.'),
    _('Your ISP does not provide you a static IP address and your IP '
      'address changes every time you connect to Internet.'),
    _('Your ISP limits incoming connections.'),
    format_lazy(
        _('PageKite works around NAT, firewalls and IP-address limitations '
          'by using a combination of tunnels and reverse proxies. You can '
          'use any pagekite service provider, for example '
          '<a href="https://pagekite.net">pagekite.net</a>.  In future it '
          'might be possible to use your buddy\'s {box_name} for this.'),
        box_name=_(cfg.box_name))
]

manual_page = 'PageKite'

app = None


class PagekiteApp(app_module.App):
    """FreedomBox app for Pagekite."""

    app_id = 'pagekite'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-pagekite', name, short_description,
                              'fa-flag', 'pagekite:index',
                              parent_url_name='system')
        self.add(menu_item)

        domain_type = DomainType('domain-type-pagekite', _('PageKite Domain'),
                                 'pagekite:index', can_have_certificate=True)
        self.add(domain_type)

        # XXX: Add pagekite daemon component and simplify action script


def init():
    """Initialize the PageKite module"""
    global app
    app = PagekiteApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)

    # Register kite name with Name Services module.
    utils.update_names_module(initial_registration=True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
