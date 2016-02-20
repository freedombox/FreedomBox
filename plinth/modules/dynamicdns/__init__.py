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
from plinth.utils import format_lazy

version = 1

depends = ['apps']

title = _('Dynamic DNS Client')

description = [
    format_lazy(
        _('If your internet provider changes your IP address periodic '
          '(i.e. every 24h) it may be hard for others to find you in the '
          'WEB. And for this reason nobody may find the services which are '
          'provided by {box_name}, such as ownCloud.'),
        box_name=_(cfg.box_name)),

    _('The solution is to assign a DNS name to your IP address and '
      'update the DNS name every time your IP is changed by your '
      'Internet provider. Dynamic DNS allows you to push your current '
      'public IP address to an '
      '<a href=\'http://gnudip2.sourceforge.net/\' target=\'_blank\'> '
      'gnudip </a> server. Afterwards the Server will assign your DNS name '
      'with the new IP and if someone from the Internet asks for your DNS '
      'name he will get your current IP answered.')
]


def init():
    """Initialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-refresh', 'dynamicdns:index', 500)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['ez-ipupdate'])
