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
Plinth module to configure ez-ipupdate client
"""

from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.menu import main_menu
from plinth.utils import format_lazy


version = 1

managed_packages = ['ez-ipupdate']

title = _('Dynamic DNS Client')

description = [
    format_lazy(
        _('If your Internet provider changes your IP address periodically '
          '(i.e. every 24h), it may be hard for others to find you on the '
          'Internet. This will prevent others from finding services which are '
          'provided by this {box_name}.'),
        box_name=_(cfg.box_name)),

    _('The solution is to assign a DNS name to your IP address and '
      'update the DNS name every time your IP is changed by your '
      'Internet provider. Dynamic DNS allows you to push your current '
      'public IP address to a '
      '<a href=\'http://gnudip2.sourceforge.net/\' target=\'_blank\'> '
      'GnuDIP</a> server. Afterwards, the server will assign your DNS name '
      'to the new IP, and if someone from the Internet asks for your DNS '
      'name, they will get a response with your current IP address.')
]

reserved_usernames = ['ez-ipupd']

def init():
    """Initialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-refresh', 'dynamicdns:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
