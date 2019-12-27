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

    app_id = None
    _all_apps = collections.OrderedDict()

    def __init__(self):
        """Initialize the app object."""
        if not self.app_id:
            raise ValueError('Invalid app ID configured')

        self.components = collections.OrderedDict()

        # Add self to global list of apps
        self._all_apps[self.app_id] = self

    @classmethod
    def get(cls, app_id):
        """Return an app with given ID."""
        return cls._all_apps[app_id]

    @classmethod
    def list(cls):
        """Return a list of all apps."""
        return cls._all_apps.values()

    def add(self, component):
        """Add a component to an app."""
        self.components[component.component_id] = component
        return self

    def remove(self, component_id):
        """Remove a component from the app."""
        component = self.components[component_id]
        del self.components[component_id]
        return component

    def get_component(self, component_id):
        """Return a component given the component's ID."""
        return self.components[component_id]

    def get_components_of_type(self, component_type):
        """Return all components of a given type."""
        for component in self.components.values():
            if isinstance(component, component_type):
                yield component

    def enable(self):
        """Enable all the components of the app."""
        for component in self.components.values():
            component.enable()

    def disable(self):
        """Enable all the components of the app."""
        for component in reversed(self.components.values()):
            component.disable()

    def is_enabled(self):
        """Return whether all the leader components are enabled.

        Return True when there are no leader components.
        """
        return all((component.is_enabled()
                    for component in self.components.values()
                    if component.is_leader))

    def set_enabled(self, enabled):
        """Update the status of all follower components.

        Do not query or update the status of the leader components.

        """
        for component in self.components.values():
            if not component.is_leader:
                component.set_enabled(enabled)

    def diagnose(self):
        """Run diagnostics and return results.

        Return value must be a list of results. Each result is a two-tuple with
        first value as user visible description of the test followed by the
        result. The test result is a string enumeration from 'failed', 'passed'
        and 'error'.

        Results are typically collected by diagnosing each component of the app
        and then supplementing the results with any app level diagnostic tests.

        Also see :meth:`.has_diagnostics`.

        """
        results = []
        for component in self.components.values():
            results.extend(component.diagnose())

        return results

    def has_diagnostics(self):
        """Return whether at least one diagnostic test is implemented.

        If this method returns True, a button or menu item is shown to the
        user to run diagnostics on this app. When the action is selected by the
        user, the :meth:`.diagnose` method is called and the results are
        presented to the user. Additionally collection of diagnostic results of
        all apps can be obtained by the user from the Diagnostics module in
        System section.

        If a component of this app implements a diagnostic test, this method
        returns True.

        Further, if a subclass of App overrides the :meth:`.diagnose` method,
        it is assumed that it is for implementing diagnostic tests and this
        method returns True for such an app. Override this method if this
        default behavior does not fit the needs.

        """
        # App implements some diagnostics
        if self.__class__.diagnose is not App.diagnose:
            return True

        # Any of the components implement diagnostics
        for component in self.components.values():
            if component.has_diagnostics():
                return True

        return False


class Component:
    """Interface for an app component."""

    is_leader = False

    def __init__(self, component_id):
        """Initialize the component."""
        if not component_id:
            raise ValueError('Invalid component ID')

        self.component_id = component_id

    def enable(self):
        """Run operations to enable the component."""
    def disable(self):
        """Run operations to disable the component."""
    @staticmethod
    def diagnose():
        """Run diagnostics and return results.

        Return value must be a list of results. Each result is a two-tuple with
        first value as user visible description of the test followed by the
        result. The test result is a string enumeration from 'failed', 'passed'
        and 'error'.

        Also see :meth:`.has_diagnostics`.

        """
        return []

    def has_diagnostics(self):
        """Return whether at least one diagnostic test is implemented.

        If this method return True, the :meth:`App.has_diagnostics`. also
        returns True.

        If a subclass of Component overrides the :meth:`.diagnose` method, it
        is assumed that it is for implementing diagnostic tests and this method
        returns True for such a component. Override this method if this default
        behavior does not fit the needs.

        """
        return self.__class__.diagnose is not Component.diagnose


class FollowerComponent(Component):
    """Interface for an app component that follows other components.

    These components of the app don't determine if the app is enabled or not.

    """

    is_leader = False

    def __init__(self, component_id, is_enabled=False):
        """Initialize the component."""
        super().__init__(component_id)
        self._is_enabled = is_enabled

    def is_enabled(self):
        """Return whether the component is enabled."""
        return self._is_enabled

    def set_enabled(self, enabled):
        """Update the internal enabled state of the component."""
        self._is_enabled = enabled

    def enable(self):
        """Run operations to enable the component."""
        self._is_enabled = True

    def disable(self):
        """Run operations to disable the component."""
        self._is_enabled = False


class LeaderComponent(Component):
    """Interface for an app component that decides the state of the app.

    These components determine if the app is enabled or not.

    """

    is_leader = True

    def is_enabled(self):
        """Return if the component is enabled."""
        raise NotImplementedError
