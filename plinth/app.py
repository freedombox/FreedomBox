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
Base class for all Freedombox applications.
"""

import collections


class App:
    """Implement common functionality for an app.

    An app is composed of components which actually performs various tasks. App
    itself delegates tasks for individual components. Applications can show a
    variation their behavior by choosing which components to have and by
    customizing the components themselves.

    """

    def __init__(self):
        """Initialize the app object."""
        self.components = collections.OrderedDict()

    def add(self, component):
        """Add a component to an app."""
        self.components[component.component_id] = component
        return self

    def enable(self):
        """Enable all the components of the app."""
        for component in self.components.values():
            component.enable()

    def disable(self):
        """Enable all the components of the app."""
        for component in self.components.values():
            component.disable()

    def is_enabled(self):
        """Return whether all the leader components are enabled."""
        return all((component.is_enabled()
                    for component in self.components.values()
                    if component.is_leader))

    def set_enabled(self, enabled):
        """Update the status of all follower components.

        Do not query or update the status of the leader components.

        """
        for component in self.components.values():
            if not component.is_leader:
                if enabled:
                    component.enable()
                else:
                    component.disable()


class Component:
    """Interface for an app component."""

    is_leader = False

    def __init__(self, component_id):
        """Intialize the component."""
        if not component_id:
            raise ValueError('Invalid component ID')

        self.component_id = component_id

    def enable(self):
        """Enable the component."""

    def disable(self):
        """Disable the component."""


class FollowerComponent(Component):
    """Interface for an app component that follows other components.

    These components of the app don't determine if the app is enabled or not.

    """

    is_leader = False

    def __init__(self, component_id, is_enabled=False):
        """Intialize the component."""
        super().__init__(component_id)
        self._is_enabled = is_enabled

    def is_enabled(self):
        """Return whether the component is enabled."""
        return self._is_enabled

    def enable(self):
        """Enable the component."""
        self._is_enabled = True

    def disable(self):
        """Disable the component."""
        self._is_enabled = False


class LeaderComponent(Component):
    """Interface for an app component that decides the state of the app.

    These components determine if the app is enabled or not.

    """

    is_leader = True

    def is_enabled(self):
        """Return if the component is enabled."""
        raise NotImplementedError
