# SPDX-License-Identifier: AGPL-3.0-or-later
"""App component for other apps to use Apache configuration functionality."""

import re
import subprocess

from django.utils.translation import gettext_noop

from plinth import action_utils, app, kvstore
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)
from plinth.privileged import service as service_privileged

from . import privileged


class Webserver(app.LeaderComponent):
    """Component to enable/disable Apache configuration."""

    def __init__(self, component_id: str, web_name: str, kind: str = 'config',
                 urls: list[str] | None = None, expect_redirects: bool = False,
                 last_updated_version: int | None = None):
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

        expect_redirects is a boolean that allows redirects when trying to
        access the URLs during diagnosis of the component.

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

    def is_enabled(self) -> bool:
        """Return whether the Apache configuration is enabled."""
        return action_utils.webserver_is_enabled(self.web_name, kind=self.kind)

    def enable(self) -> None:
        """Enable the Apache configuration."""
        privileged.enable(self.web_name, self.kind)

    def disable(self) -> None:
        """Disable the Apache configuration."""
        privileged.disable(self.web_name, self.kind)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Check if the web path is accessible by clients.

        See :py:meth:`plinth.app.Component.diagnose`.
        """
        results = []
        for url in self.urls:
            if '{host}' in url:
                results.extend(
                    diagnose_url_on_all(url, check_certificate=False,
                                        expect_redirects=self.expect_redirects,
                                        component_id=self.component_id))
            else:
                results.append(
                    diagnose_url(url, check_certificate=False,
                                 component_id=self.component_id))

        return results

    def setup(self, old_version: int):
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


class WebserverRoot(app.FollowerComponent):
    """Component to enable/disable Apache configuration for domain root.

    Each domain has a unique virtual host configuration in Apache. This file
    includes an option configuration file that can dropped in by FreedomBox. If
    an app wants to be hosted on a dedicated domain, it can provide a
    configuration file that is meant to be in the <VirtualHost> section. Using
    this component, the include file fragment for a selected domain can be
    linked to app's configuration file. Then, for the selected domain, the
    app's configuration becomes the domain's root configuration.

    This components uses key/value store to remember the selected domain. When
    the domain changes, the change must be notified using domain_set().
    """

    def __init__(self, component_id: str, web_name: str,
                 expect_redirects: bool = False,
                 last_updated_version: int | None = None):
        """Initialize the web server component for domain root.

        component_id should be a unique ID across all components of an app and
        across all components.

        web_name is the primary part of the configuration file path which must
        be enabled/disabled by this component. The file's path should be
        /etc/apache2/includes/<web_name>.conf.

        expect_redirects is a boolean that allows redirects when trying to
        access the domain URL during diagnosis of the component.

        last_updated_version is the app version in which the web server
        configuration/site/module file was updated. Using this, web server will
        be automatically reloaded or restarted as necessary during app upgrade.
        """
        super().__init__(component_id)

        self.web_name = web_name
        self.expect_redirects = expect_redirects
        self.last_updated_version = last_updated_version or 0

    def enable(self) -> None:
        """Link the Apache site root configuration to app configuration."""
        domain = self.domain_get()
        if domain:
            privileged.link_root(domain, self.web_name)

    def disable(self) -> None:
        """Unlink the Apache site root configuration from app configuration."""
        domain = self.domain_get()
        if domain:
            privileged.unlink_root(domain)

    def _key_get(self) -> str:
        """Return the key used to store the domain in kvstore."""
        return f'{self.component_id}_domain'

    def domain_get(self) -> str | None:
        """Return the currently configured domain name."""
        return kvstore.get_default(self._key_get(), None)

    def domain_set(self, domain: str | None):
        """Set the domain to use with the app."""
        self.disable()
        kvstore.set(self._key_get(), domain)
        if self.app.is_enabled():
            self.enable()

    def diagnose(self) -> list[DiagnosticCheck]:
        """Check if the site root path is accessible by clients.

        See :py:meth:`plinth.app.Component.diagnose`.
        """
        results = []
        domain = self.domain_get()
        if domain:
            results.append(
                diagnose_url(f'https://{domain}', check_certificate=False,
                             component_id=self.component_id))

        return results

    def setup(self, old_version: int):
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

        service_privileged.reload('apache2')

    def uninstall(self):
        """Remove the domain configured."""
        kvstore.delete(self._key_get(), ignore_missing=True)


class Uwsgi(app.LeaderComponent):
    """Component to enable/disable uWSGI configuration."""

    def __init__(self, component_id: str, uwsgi_name: str):
        """Initialize the uWSGI component.

        component_id should be a unique ID across all components of an app and
        across all components.

        uwsgi_name is the primary part of the configuration file path which
        must be enabled/disabled by this component.

        """
        super().__init__(component_id)

        self.uwsgi_name = uwsgi_name

    def is_enabled(self) -> bool:
        """Return whether the uWSGI configuration is enabled."""
        return action_utils.uwsgi_is_enabled(self.uwsgi_name) \
            and action_utils.service_is_enabled('uwsgi')

    def enable(self) -> None:
        """Enable the uWSGI configuration."""
        privileged.uwsgi_enable(self.uwsgi_name)

    def disable(self) -> None:
        """Disable the uWSGI configuration."""
        privileged.uwsgi_disable(self.uwsgi_name)

    def is_running(self) -> bool:
        """Return whether the uWSGI daemon is running with configuration."""
        return action_utils.uwsgi_is_enabled(self.uwsgi_name) \
            and action_utils.service_is_running('uwsgi')


def diagnose_url(url: str, kind: str | None = None,
                 env: dict[str, str] | None = None,
                 check_certificate: bool = True,
                 extra_options: list[str] | None = None,
                 wrapper: str | None = None,
                 expected_output: str | None = None,
                 component_id: str | None = None) -> DiagnosticCheck:
    """Run a diagnostic on whether a URL is accessible.

    Kind can be '4' for IPv4 or '6' for IPv6.
    """
    try:
        return_value = check_url(url, kind, env, check_certificate,
                                 extra_options, wrapper, expected_output)
        result = Result.PASSED if return_value else Result.FAILED
    except FileNotFoundError:
        result = Result.ERROR

    parameters: DiagnosticCheckParameters = {'url': url, 'kind': kind}
    if kind:
        check_id = f'apache-url-kind-{url}-{kind}'
        description = gettext_noop('Access URL {url} on tcp{kind}')
    else:
        check_id = f'apache-url-{url}'
        description = gettext_noop('Access URL {url}')

    return DiagnosticCheck(check_id, description, result, parameters,
                           component_id)


def diagnose_url_on_all(url: str, expect_redirects: bool = False,
                        component_id: str | None = None,
                        **kwargs) -> list[DiagnosticCheck]:
    """Run a diagnostic on whether a URL is accessible."""
    results = []
    for address in action_utils.get_addresses():
        current_url = url.format(host=address['url_address'])
        diagnose_kwargs = dict(kwargs)
        if not expect_redirects:
            diagnose_kwargs.setdefault('kind', address['kind'])

        results.append(
            diagnose_url(current_url, component_id=component_id,
                         **diagnose_kwargs))

    return results


def check_url(url: str, kind: str | None = None,
              env: dict[str, str] | None = None,
              check_certificate: bool = True,
              extra_options: list[str] | None = None,
              wrapper: str | None = None,
              expected_output: str | None = None) -> bool:
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
