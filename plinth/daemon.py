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
Component for managing a background daemon or any systemd unit.
"""

from plinth import action_utils, actions, app


class Daemon(app.LeaderComponent):
    """Component to manage a background daemon or any systemd unit."""

    def __init__(self, component_id, unit, strict_check=False):
        """Initialize a new daemon component.

        'component_id' must be a unique string across all apps and components
        of a app. Conventionally starts with 'daemon-'.

        'unit' must the name of systemd unit that this component should manage.

        """
        super().__init__(component_id)

        self.unit = unit
        self.strict_check = strict_check

    def is_enabled(self):
        """Return if the daemon/unit is enabled."""
        return action_utils.service_is_enabled(self.unit,
                                               strict_check=self.strict_check)

    def enable(self):
        """Run operations to enable the daemon/unit."""
        actions.superuser_run('service', ['enable', self.unit])

    def disable(self):
        """Run operations to disable the daemon/unit."""
        actions.superuser_run('service', ['disable', self.unit])

    def is_running(self):
        """Return whether the daemon/unit is running."""
        return action_utils.service_is_running(self.unit)


def app_is_running(app_):
    """Return whether all the daemons in the app are running."""
    for component in app_.components.values():
        if hasattr(component, 'is_running') and not component.is_running():
            return False

    return True
