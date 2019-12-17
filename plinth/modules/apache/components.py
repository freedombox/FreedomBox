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

import re
import subprocess

from django.utils.translation import ugettext as _

from plinth import action_utils, actions, app


class Webserver(app.LeaderComponent):
    """Component to enable/disable Apache configuration."""
    def __init__(self, component_id, web_name, kind='config', urls=None):
        """Initialize the web server component.

        component_id should be a unique ID across all components of an app and
        across all components.

        web_name is the primary part of the configuration file path which must
        be enabled/disabled by this component.

        kind is the type of Apache configuration being enabled/disabled. This
        must be 'config' for a configuration in /etc/apache/conf-available/,
        'module' for configuration in /etc/apache2/mods-available/, 'site' for
        configuration in /etc/apache2/sites-available/.

        urls is a list of URLs over which a HTTP services will be available due
        to this component. This list is only used for running diagnostics.

        """
        super().__init__(component_id)

        self.web_name = web_name
        self.kind = kind
        self.urls = urls or []

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

    def diagnose(self):
        """Check if the web path is accessible by clients.

        See :py:meth:`plinth.app.Component.diagnose`.

        """
        results = []
        for url in self.urls:
            if '{host}' in url:
                results.extend(
                    diagnose_url_on_all(url, check_certificate=False))
            else:
                results.append(diagnose_url(url, check_certificate=False))

        return results


class Uwsgi(app.LeaderComponent):
    """Component to enable/disable uWSGI configuration."""
    def __init__(self, component_id, uwsgi_name):
        """Initialize the uWSGI component.

        component_id should be a unique ID across all components of an app and
        across all components.

        uwsgi_name is the primary part of the configuration file path which
        must be enabled/disabled by this component.

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


def diagnose_url(url, kind=None, env=None, check_certificate=True,
                 extra_options=None, wrapper=None, expected_output=None):
    """Run a diagnostic on whether a URL is accessible.

    Kind can be '4' for IPv4 or '6' for IPv6.
    """
    result = check_url(url, kind, env, check_certificate, extra_options,
                       wrapper, expected_output)

    if kind:
        return [
            _('Access URL {url} on tcp{kind}').format(url=url, kind=kind),
            result
        ]

    return [_('Access URL {url}').format(url=url), result]


def diagnose_url_on_all(url, **kwargs):
    """Run a diagnostic on whether a URL is accessible."""
    results = []
    for address in action_utils.get_addresses():
        current_url = url.format(host=address['url_address'])
        results.append(
            diagnose_url(current_url, kind=address['kind'], **kwargs))

    return results


def check_url(url, kind=None, env=None, check_certificate=True,
              extra_options=None, wrapper=None, expected_output=None):
    """Check whether a URL is accessible."""
    command = ['curl', '--location', '-f', '-w', '%{response_code}']

    if kind == '6':
        # extract zone index
        match = re.match(r'(.*://)\[(.*)%(?P<zone>.*)\](.*)', url)
        if match:
            command = command + ['--interface', match.group('zone')]
            url = '{0}[{1}]{2}'.format(*match.group(1, 2, 4))

    command.append(url)

    if wrapper:
        command.insert(0, wrapper)

    if not check_certificate:
        command.append('-k')

    if extra_options:
        command.extend(extra_options)

    if kind:
        command.append({'4': '-4', '6': '-6'}[kind])

    try:
        process = subprocess.run(command, env=env, check=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        result = 'passed'
        if expected_output and expected_output not in process.stdout.decode():
            result = 'failed'
    except subprocess.CalledProcessError as exception:
        result = 'failed'
        # Authorization failed is a success
        if exception.stdout.decode().strip() in ('401', '405'):
            result = 'passed'
    except FileNotFoundError:
        result = 'error'

    return result
