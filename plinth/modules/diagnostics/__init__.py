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
FreedomBox app for system diagnostics.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils
from plinth import app as app_module
from plinth import menu

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

name = _('Diagnostics')

description = [
    _('The system diagnostic test will run a number of checks on your '
      'system to confirm that applications and services are working as '
      'expected.')
]

manual_page = 'Diagnostics'

app = None


class DiagnosticsApp(app_module.App):
    """FreedomBox app for diagnostics."""

    app_id = 'diagnostics'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-diagnostics', name, None, 'fa-heartbeat',
                              'diagnostics:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the module"""
    global app
    app = DiagnosticsApp()
    app.set_enabled(True)


def diagnose():
    """Run diagnostics and return the results."""
    results = []
    results.append(action_utils.diagnose_port_listening(8000, 'tcp4'))
    results.extend(
        action_utils.diagnose_url_on_all('http://{host}/plinth/',
                                         check_certificate=False))

    return results
