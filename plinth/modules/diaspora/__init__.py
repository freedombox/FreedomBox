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

import os

from django.utils.translation import ugettext_lazy as _

from plinth.utils import format_lazy
from plinth import actions, action_utils, frontpage, \
    service as service_module
from plinth.errors import DomainNotRegisteredError
from plinth.menu import main_menu

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

title_en = 'Federated Social Network \n (diaspora*)'

title = _(title_en)

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


def init():
    """Initialize the Diaspora module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-thumbs-up', 'diaspora:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'diaspora', ['pre-install'])
    helper.install(managed_packages)
    helper.call('custom_config', actions.superuser_run, 'diaspora',
                ['disable-ssl'])
    helper.call('post', actions.superuser_run, 'diaspora', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Add shortcut to diaspora on the Plinth homepage"""
    if is_setup():
        frontpage.add_shortcut(
            'diaspora', title,
            url='https://diaspora.{}'.format(get_configured_domain_name()),
            login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('diaspora-plinth')


def enable():
    """Enable the module."""
    actions.superuser_run('diaspora', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('diaspora', ['disable'])
    frontpage.remove_shortcut('diaspora')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(
        action_utils.diagnose_url(
            'http://diaspora.localhost', kind='4', check_certificate=False))
    results.append(
        action_utils.diagnose_url(
            'http://diaspora.localhost', kind='6', check_certificate=False))
    results.append(
        action_utils.diagnose_url(
            'http://diaspora.{}'.format(get_configured_domain_name()),
            kind='4',
            check_certificate=False))

    return results
