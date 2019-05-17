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

import os

import augeas
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth import service as service_module
from plinth.errors import DomainNotRegisteredError
from plinth.utils import format_lazy

domain_name_file = "/etc/diaspora/domain_name"
lazy_domain_name = None  # To avoid repeatedly reading from file


def is_setup():
    return os.path.exists(domain_name_file)


def get_configured_domain_name():
    global lazy_domain_name
    if lazy_domain_name:
        return lazy_domain_name

    if not is_setup():
        raise DomainNotRegisteredError()

    with open(domain_name_file) as dnf:
        lazy_domain_name = dnf.read().rstrip()
        return lazy_domain_name


version = 1

name = _('diaspora*')

short_description = _('Federated Social Network')

service = None

managed_services = ['diaspora']

managed_packages = ['diaspora']

description = [
    _('diaspora* is a decentralized social network where you can store '
      'and control your own data.'),
    format_lazy(
        'When enabled, the diaspora* pod will be available from '
        '<a href="https://diaspora.{host}">diaspora.{host}</a> path on the '
        'web server.'.format(host=get_configured_domain_name()) if is_setup()
        else 'Please register a domain name for your FreedomBox to be able to'
        ' federate with other diaspora* pods.')
]

from .manifest import clients  # isort:skip
clients = clients

app = None


class DiasporaApp(app_module.App):
    """FreedomBox app for Diaspora."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-diaspora', name, short_description,
                              'diaspora', 'diaspora:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = Shortcut(
            'shortcut-diaspora', name, short_description=short_description,
            icon='diaspora', url=None, clients=clients, login_required=True)
        self.add(shortcut)


class Shortcut(frontpage.Shortcut):
    """Frontpage shortcut to use configured domain name for URL."""

    def enable(self):
        """Set the proper shortcut URL when enabled."""
        super().enable()
        self.url = 'https://diaspora.{}'.format(get_configured_domain_name())


def init():
    """Initialize the Diaspora module."""
    global app
    app = DiasporaApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)

        if is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'diaspora', ['pre-install'])
    helper.install(managed_packages)
    helper.call('custom_config', actions.superuser_run, 'diaspora',
                ['disable-ssl'])


def setup_domain_name(domain_name):
    actions.superuser_run('diaspora', ['setup', '--domain-name', domain_name])
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    service.notify_enabled(None, True)
    app.enable()


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('diaspora-plinth')


def enable():
    """Enable the module."""
    actions.superuser_run('diaspora', ['enable'])
    app.enable()


def disable():
    """Disable the module."""
    actions.superuser_run('diaspora', ['disable'])
    app.disable()


def is_user_registrations_enabled():
    """Return whether user registrations are enabled"""
    with open('/etc/diaspora/diaspora.yml') as f:
        for line in f.readlines():
            if "enable_registrations" in line:
                return line.split(":")[1].strip() == "true"


def enable_user_registrations():
    """Allow users to register without invitation"""
    actions.superuser_run('diaspora', ['enable-user-registrations'])


def disable_user_registrations():
    """Disallow users from registering without invitation"""
    actions.superuser_run('diaspora', ['disable-user-registrations'])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(
        action_utils.diagnose_url('http://diaspora.localhost', kind='4',
                                  check_certificate=False))
    results.append(
        action_utils.diagnose_url('http://diaspora.localhost', kind='6',
                                  check_certificate=False))
    results.append(
        action_utils.diagnose_url(
            'http://diaspora.{}'.format(get_configured_domain_name()),
            kind='4', check_certificate=False))

    return results


def generate_apache_configuration(conf_file, domain_name):
    """Generate Diaspora's apache configuration with the given domain name"""
    open(conf_file, 'w').close()

    diaspora_domain_name = ".".join(["diaspora", domain_name])

    aug = augeas.Augeas(
        flags=augeas.Augeas.NO_LOAD + augeas.Augeas.NO_MODL_AUTOLOAD)

    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    aug.set('/augeas/load/Httpd/incl[last() + 1]', conf_file)
    aug.load()

    aug.defvar('conf', '/files' + conf_file)

    aug.set('$conf/VirtualHost', None)
    aug.defvar('vh', '$conf/VirtualHost')
    aug.set('$vh/arg', diaspora_domain_name)
    aug.set('$vh/directive[1]', 'ServerName')
    aug.set('$vh/directive[1]/arg', diaspora_domain_name)
    aug.set('$vh/directive[2]', 'DocumentRoot')
    aug.set('$vh/directive[2]/arg', '"/var/lib/diaspora/public/"')

    aug.set('$vh/Location', None)
    aug.set('$vh/Location/arg', '"/"')
    aug.set('$vh/Location/directive[1]', 'ProxyPass')
    aug.set('$vh/Location/directive[1]/arg',
            '"unix:/var/run/diaspora/diaspora.sock|http://localhost/"')

    aug.set('$vh/Location[last() + 1]', None)
    aug.set('$vh/Location[last()]/arg', '"/assets"')
    aug.set('$vh/Location[last()]/directive[1]', 'ProxyPass')
    aug.set('$vh/Location[last()]/directive[1]/arg', '!')

    aug.set('$vh/Directory', None)
    aug.set('$vh/Directory/arg', '/var/lib/diaspora/public/')
    aug.set('$vh/Directory/directive[1]', 'Require')
    aug.set('$vh/Directory/directive[1]/arg[1]', 'all')
    aug.set('$vh/Directory/directive[1]/arg[2]', 'granted')

    aug.save()
