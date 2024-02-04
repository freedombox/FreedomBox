# SPDX-License-Identifier: AGPL-3.0-or-later
"""App component for other apps to use Apache configuration functionality."""

import re
import subprocess

from django.utils.translation import gettext_noop

from plinth import action_utils, app
from plinth.modules.diagnostics.check import DiagnosticCheck, Result
from plinth.privileged import service as service_privileged

from . import privileged


class Webserver(app.LeaderComponent):
    """Component to enable/disable Apache configuration."""

    def __init__(self, component_id, web_name, kind='config', urls=None,
                 expect_redirects=False, last_updated_version=None):
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

        last_updated_version is the app version in which the web server
        configuration/site/module file was updated. Using this, web server will
        be automatically reloaded or restarted as necessary during app upgrade.
        """
        super().__init__(component_id)

        self.web_name = web_name
        self.kind = kind
        self.urls = urls or []
        self.expect_redirects = expect_redirects
        self.last_updated_version = last_updated_version or 0

    def is_enabled(self):
        """Return whether the Apache configuration is enabled."""
        return action_utils.webserver_is_enabled(self.web_name, kind=self.kind)

    def enable(self):
        """Enable the Apache configuration."""
        privileged.enable(self.web_name, self.kind)

    def disable(self):
        """Disable the Apache configuration."""
        privileged.disable(self.web_name, self.kind)

    def diagnose(self):
        """Check if the web path is accessible by clients.

        See :py:meth:`plinth.app.Component.diagnose`.

        """
        results = []
        for url in self.urls:
            if '{host}' in url:
                results.extend(
                    diagnose_url_on_all(
                        url, check_certificate=False,
                        expect_redirects=self.expect_redirects))
            else:
                results.append(diagnose_url(url, check_certificate=False))

        return results

    def setup(self, old_version):
        """Restart/reload web server if configuration files changed."""
        if not old_version:
            # App is being freshly setup. After setup, app will be enabled
            # which will result in reload/restart of web server.
            return

        if old_version >= self.last_updated_version:
            # Already using the latest configuration. Web server reload/restart
            # is not necessary.
            return

        if not self.app.is_enabled():
            # App is currently disabled, web server will reloaded/restarted
            # when the app is enabled.
            return

        if self.kind == 'module':
            service_privileged.restart('apache2')
        else:
            service_privileged.reload('apache2')


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
        privileged.uwsgi_enable(self.uwsgi_name)

    def disable(self):
        """Disable the uWSGI configuration."""
        privileged.uwsgi_disable(self.uwsgi_name)

    def is_running(self):
        """Return whether the uWSGI daemon is running with configuration."""
        return action_utils.uwsgi_is_enabled(self.uwsgi_name) \
            and action_utils.service_is_running('uwsgi')


def diagnose_url(url, kind=None, env=None, check_certificate=True,
                 extra_options=None, wrapper=None, expected_output=None):
    """Run a diagnostic on whether a URL is accessible.

    Kind can be '4' for IPv4 or '6' for IPv6.
    """
    try:
        return_value = check_url(url, kind, env, check_certificate,
                                 extra_options, wrapper, expected_output)
        result = Result.PASSED if return_value else Result.FAILED
    except FileNotFoundError:
        result = Result.ERROR

    parameters = {'url': url, 'kind': kind}
    if kind:
        check_id = f'apache-url-kind-{url}-{kind}'
        description = gettext_noop('Access URL {url} on tcp{kind}')
    else:
        check_id = f'apache-url-{url}'
        description = gettext_noop('Access URL {url}')

    return DiagnosticCheck(check_id, description, result, parameters)


def diagnose_url_on_all(url, expect_redirects=False, **kwargs):
    """Run a diagnostic on whether a URL is accessible."""
    results = []
    for address in action_utils.get_addresses():
        current_url = url.format(host=address['url_address'])
        diagnose_kwargs = dict(kwargs)
        if not expect_redirects:
            diagnose_kwargs.setdefault('kind', address['kind'])

        results.append(diagnose_url(current_url, **diagnose_kwargs))

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
        result = True
        if expected_output and expected_output not in process.stdout.decode():
            result = False
    except subprocess.CalledProcessError as exception:
        result = False
        # Authorization failed is a success
        if exception.stdout.decode().strip() in ('401', '405'):
            result = True

    return result
