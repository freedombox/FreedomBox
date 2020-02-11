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
FreedomBox app for power controls.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

_description = [_('Restart or shut down the system.')]

app = None


class PowerApp(app_module.App):
    """FreedomBox app for power controls."""

    app_id = 'power'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Power'),
                               description=_description, manual_page='Power')
        self.add(info)

        # not in menu, see issue #834


def init():
    """Initialize the power module."""
    global app
    app = PowerApp()
    app.set_enabled(True)
