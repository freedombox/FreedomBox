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
FreedomBox app to configure ejabberd server.
"""

import logging
import socket

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.signals import (domainname_change, post_hostname_change,
                            pre_hostname_change)
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_services = ['ejabberd']

managed_packages = ['ejabberd']

name = _('ejabberd')

short_description = _('Chat Server')

description = [
    _('XMPP is an open and standardized communication protocol. Here '
      'you can run and configure your XMPP server, called ejabberd.'),
    format_lazy(
        _('To actually communicate, you can use the <a href="{jsxc_url}">'
          'web client</a> or any other <a href=\'https://xmpp.org/'
          'software/clients\' target=\'_blank\'>XMPP client</a>. '
          'When enabled, ejabberd can be accessed by any <a href="{users_url}">'
          'user with a {box_name} login</a>.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index'),
        jsxc_url=reverse_lazy('jsxc:index'))
]

clients = clients

reserved_usernames = ['ejabberd']

service = None

manual_page = 'ejabberd'

logger = logging.getLogger(__name__)


def init():
    """Initialize the ejabberd module"""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'ejabberd', 'ejabberd:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'ejabberd', name,
            ports=['xmpp-client', 'xmpp-server',
                   'xmpp-bosh'], is_external=True, is_enabled=is_enabled,
            enable=enable, disable=disable)
        if is_enabled():
            add_shortcut()
    pre_hostname_change.connect(on_pre_hostname_change)
    post_hostname_change.connect(on_post_hostname_change)
    domainname_change.connect(on_domainname_change)


def setup(helper, old_version=None):
    """Install and configure the module."""
    domainname = get_domainname()
    logger.info('ejabberd service domainname - %s', domainname)

    helper.call('pre', actions.superuser_run, 'ejabberd',
                ['pre-install', '--domainname', domainname])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ejabberd', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            'ejabberd', name,
            ports=['xmpp-client', 'xmpp-server',
                   'xmpp-bosh'], is_external=True, is_enabled=is_enabled,
            enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut(
        'ejabberd', name=name, short_description=short_description,
        details=description, configure_url=reverse_lazy('ejabberd:index'),
        login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('ejabberd')


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def enable():
    """Enable the module."""
    actions.superuser_run('ejabberd', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('ejabberd', ['disable'])
    frontpage.remove_shortcut('ejabberd')


def on_pre_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """
    Backup ejabberd database before hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('ejabberd', [
        'pre-change-hostname', '--old-hostname', old_hostname,
        '--new-hostname', new_hostname
    ])


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """Update ejabberd config after hostname change."""
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('ejabberd', [
        'change-hostname', '--old-hostname', old_hostname, '--new-hostname',
        new_hostname
    ], run_in_background=True)


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Update ejabberd config after domain name change."""
    del sender  # Unused
    del old_domainname  # Unused
    del kwargs  # Unused

    actions.superuser_run(
        'ejabberd', ['change-domainname', '--domainname', new_domainname],
        run_in_background=True)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5222, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5222, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all('http://{host}/bosh/'))

    return results
