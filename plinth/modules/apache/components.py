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
App component for other apps to use Apache configuration functionality.
"""

from plinth import action_utils, actions, app


class Webserver(app.LeaderComponent):
    """Component to enable/disable Apache configuration."""

    def __init__(self, component_id, web_name, kind='config'):
        """Initialize the web server component.

        component_id should be a unique ID across all components of an app and
        across all components.

        web_name is the primary part of the configuration file path which must
        be enabled/disabled by this component.

        kind is the type of Apache configuration being enabled/disabled. This
        must be 'config' for a configuration in /etc/apache/conf-available/,
        'module' for configuration in /etc/apache2/mods-available/, 'site' for
        configuration in /etc/apache2/sites-available/.

        """
        super().__init__(component_id)

        self.web_name = web_name
        self.kind = kind

    def is_enabled(self):
        """Return whether the Apache configuration is enabled."""
        return action_utils.webserver_is_enabled(self.web_name, kind=self.kind)

    def enable(self):
        """Enable the Apache configuration."""
        actions.superuser_run(
            'apache', ['enable', '--name', self.web_name, '--kind', self.kind])

    def disable(self):
        """Disable the Apache configuration."""
        actions.superuser_run(
            'apache',
            ['disable', '--name', self.web_name, '--kind', self.kind])


class Uwsgi(app.LeaderComponent):
    """Component to enable/disable uWSGI configuration."""

    def __init__(self, component_id, uwsgi_name):
        """Initialize the uWSGI component.

        component_id should be a unique ID across all components of an app and
        across all components.

        uwsgi_name is the primary part of the configuration file path which must
        be enabled/disabled by this component.

        """
        super().__init__(component_id)

        self.uwsgi_name = uwsgi_name

    def is_enabled(self):
        """Return whether the uWSGI configuration is enabled."""
        return action_utils.uwsgi_is_enabled(self.uwsgi_name) \
            and action_utils.service_is_enabled('uwsgi')

    def enable(self):
        """Enable the uWSGI configuration."""
        actions.superuser_run('apache',
                              ['uwsgi-enable', '--name', self.uwsgi_name])

    def disable(self):
        """Disable the uWSGI configuration."""
        actions.superuser_run('apache',
                              ['uwsgi-disable', '--name', self.uwsgi_name])

    def is_running(self):
        """Return whether the uWSGI daemon is running with configuration."""
        return action_utils.uwsgi_is_enabled(self.uwsgi_name) \
            and action_utils.service_is_running('uwsgi')
