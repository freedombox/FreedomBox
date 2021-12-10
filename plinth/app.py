# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Base class for all Freedombox applications.
"""

import collections

from . import clients as clients_module


class App:
    """Implement common functionality for an app.

    An app is composed of components which actually performs various tasks. App
    itself delegates tasks for individual components. Applications can show a
    variation in their behavior by choosing which components to have and by
    customizing the components themselves.

    'app_id' property of the app must be a string that is a globally unique ID.
    This is typically also the name of the python module handling the app. So,
    it should be all lower-case English alphabet and digits without any special
    characters.

    'can_be_disabled' is a boolean indicating whether an app can be disabled by
    the user. Enable/disable button for this app will not be shown. Default
    value is True, so the app can be disabled.

    'locked' is a boolean indicating whether the user can perform operations on
    the app. This flag is currently set during backup and restore operations
    but UI changes are currently not implemented.

    """

    app_id = None

    can_be_disabled = True

    locked = False  # Whether user interaction with the app is allowed.
    # XXX: Lockdown the application UI by implementing a middleware

    _all_apps = collections.OrderedDict()

    def __init__(self):
        """Build the app by adding components.

        App may be built just for the purpose for querying. For example, when
        querying the list of package dependencies of essential apps, an app is
        minimally constructed under a read-only environment for querying from a
        specific component. So, this operation should have no side-effects such
        connecting to signals, running configuration corrections and scheduling
        operations.
        """
        if not self.app_id:
            raise ValueError('Invalid app ID configured')

        self.components = collections.OrderedDict()

        # Add self to global list of apps
        self._all_apps[self.app_id] = self

    def post_init(self):
        """Perform post initialization operations.

        Additional initialization operations such as connecting to signals,
        running configuration corrections and scheduling operations should be
        done in this method rather than in __init__().
        """

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
        component.app_id = self.app_id
        self.components[component.component_id] = component
        return self

    def remove(self, component_id):
        """Remove a component from the app."""
        component = self.components[component_id]
        component.app_id = None
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

    @property
    def info(self):
        """Return the information component of the app.

        It is mandatory to have one :class:`~plinth.app.Info` component in
        every app to provide basic information about the app. Trying to access
        this property without having the Info component will result in a
        KeyError exception being raised. The lookup for the Info component is
        performed using the auto-generated component_id assigned to the Info
        component based on the app_id.

        """
        return self.get_component(self.app_id + '-info')

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
        result. The test result is a string enumeration from 'failed',
        'passed', 'error' and 'warning'.

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
    """Interface for an app component.

    `app_id` is a string which is set to the value of the application's app_id
    to which this component belongs. It is set when the component is added to
    an app. When the component is removed from an app, it set to None.

    """

    is_leader = False

    def __init__(self, component_id):
        """Initialize the component."""
        if not component_id:
            raise ValueError('Invalid component ID')

        self.component_id = component_id
        self.app_id = None

    @property
    def app(self):
        """Return the app this component is part of.

        Raises KeyError if this component is not part of any app.

        """
        return App.get(self.app_id)

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


class Info(FollowerComponent):
    """Component to capture basic information about an app."""

    def __init__(self, app_id, version, is_essential=False, depends=None,
                 name=None, icon=None, icon_filename=None,
                 short_description=None, description=None, manual_page=None,
                 clients=None, donation_url=None):
        """Store the basic properties of an app as a component.

        Each app must contain at least one component of this type to provide
        basic information about the app such as it's version number.

        Instead of polluting the list of properties of an app, this component
        stores them separately. This component can also be safely passed around
        to template etc. without exposing the methods of an app and without
        creating unnecessarily cyclic dependencies.

        'app_id' must be the unique ID of the app to which this information
        belongs.

        'version' is the monotonically increasing positive integer starting at
        1. It represents the version number of the app. It is used by the setup
        mechanism. When an app's version number is increased, the setup
        mechanism assumes that the setup() method of the app needs to run
        again. This is used to upgrade/change configuration/setup of a app
        when a new version of the app is deployed on users' machine.

        'is_essential' is a boolean that marks the app as mandatory for the
        basic functions of the system. If True, this app will be installed and
        setup during the first run of FreedomBox even before first setup wizard
        is shown to the user.

        'depends' is the list of other apps that this app depends on. Apps from
        this list are guaranteed to be initialized before initializing the app
        to which this component belongs.

        'name' is the user visible name of this app. It is shown as the title
        of the app in the list of apps and when viewing app details. It should
        be a lazily translated Django string.

        'icon' is the name of icon to use with this app from a predetermined
        list of icons. This is currently an icon class name from the Fork
        Awesome font. It is used when showing the app in the System section.
        Each app typically has either an 'icon' or 'icon_filename' property
        set.

        'icon_filename' is the name of the icon file, without the suffix, to be
        used with this app. A .svg file (used in the web interface) and a .png
        file (currently used by Android App) must be provided by the app. It is
        used in the primary app page and on the app listing page. Each app
        typically has either an 'icon' or 'icon_filename' property set.

        'short_description' is the user visible generic name of the app. For
        example, for the 'Tor' app the short description is 'Anonymity
        Network'. It is shown along with the name of the app in the list of
        apps and when viewing the app's main page. It should be a lazily
        translated Django string.

        'description' is the user visible full description of the app. It is
        shown along in the app page along with other app details. It should be
        a list of lazily translated Django strings. Each string is rendered as
        a paragraph on the page. It may contain HTML <a> tags to provide links
        to external content.

        'manual_page' is the optional name of the page for this app in the user
        manual. If provided, a 'Learn more...' link appears in the app page for
        this app.

        'clients' is the list of applications that can be used with the
        services provided by this app. This is used to suggest installation of
        compatible clients on desktop, web and mobile. This is a list of
        dictionaries who structure is documented in plinth.clients.

        'donation_url' is a link to a webpage that describes how to
        donate to the upstream project.

        """
        self.component_id = app_id + '-info'
        self.app_id = app_id
        self.version = version
        self.is_essential = is_essential
        self.depends = depends or []
        self.name = name
        self.icon = icon
        self.icon_filename = icon_filename
        self.short_description = short_description
        self.description = description
        self.manual_page = manual_page
        self.clients = clients
        self.donation_url = donation_url
        if clients:
            clients_module.validate(clients)
