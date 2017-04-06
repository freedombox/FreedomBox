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
Plinth module to configure PageKite
"""

from django.utils.translation import ugettext_lazy as _

from . import utils
from plinth import cfg
from plinth.menu import main_menu
from plinth.utils import format_lazy


version = 1

depends = ['names']

managed_packages = ['pagekite']

first_boot_steps = [
    {
        'id': 'pagekite_firstboot',
        'url': 'pagekite:firstboot',
        'order': 5,
    },
]

title = _('Public Visibility (PageKite)')

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
      'address changes evertime you connect to Internet.'),

    _('Your ISP limits incoming connections.'),

    format_lazy(
        _('PageKite works around NAT, firewalls and IP-address limitations '
          'by using a combination of tunnels and reverse proxies. You can '
          'use any pagekite service provider, for example '
          '<a href="https://pagekite.net">pagekite.net</a>.  In future it '
          'might be possible to use your buddy\'s {box_name} for this.'),
        box_name=_(cfg.box_name))
]


def init():
    """Intialize the PageKite module"""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-flag', 'pagekite:index')

    # Register kite name with Name Services module.
    utils.update_names_module(initial_registration=True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
