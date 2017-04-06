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
Plinth module for system diagnostics
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils
from plinth.menu import main_menu


version = 1

is_essential = True

title = _('Diagnostics')

description = [
    _('The system diagnostic test will run a number of checks on your '
      'system to confirm that applications and services are working as '
      'expected.')
]


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-screenshot', 'diagnostics:index')


def diagnose():
    """Run diagnostics and return the results."""
    results = []
    results.append(action_utils.diagnose_port_listening(8000, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(8000, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'http://{host}/plinth/', check_certificate=False))

    return results
