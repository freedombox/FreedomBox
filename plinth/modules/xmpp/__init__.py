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
Plinth module to configure XMPP server
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
import logging
import socket

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change


version = 2

depends = ['apps']

managed_services = ['ejabberd']

managed_packages = ['libjs-jsxc', 'ejabberd']

title = _('Chat Server (XMPP)')

description = [
    _('XMPP is an open and standardized communication protocol. Here '
      'you can run and configure your XMPP server, called ejabberd.'),

    _('To actually communicate, you can use the web client or any other '
      '<a href=\'http://xmpp.org/xmpp-software/clients/\' target=\'_blank\''
      '>XMPP client</a>.'),
]

service = None

logger = logging.getLogger(__name__)


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-comment', 'xmpp:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'ejabberd', title,
            ports=['xmpp-client', 'xmpp-server', 'xmpp-bosh'],
            is_external=True, is_enabled=is_enabled, enable=enable,
            disable=disable)
        if is_enabled():
            add_shortcut()
    pre_hostname_change.connect(on_pre_hostname_change)
    post_hostname_change.connect(on_post_hostname_change)
    domainname_change.connect(on_domainname_change)


def setup(helper, old_version=None):
    """Install and configure the module."""
    domainname = get_domainname()
    logger.info('XMPP service domainname - %s', domainname)

    helper.call('pre', actions.superuser_run, 'xmpp',
                ['pre-install', '--domainname', domainname])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'xmpp', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            'ejabberd', title,
            ports=['xmpp-client', 'xmpp-server', 'xmpp-bosh'],
            is_external=True, is_enabled=is_enabled, enable=enable,
            disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('jsxc', _('Chat Client (jsxc)'),
                           reverse_lazy('xmpp:jsxc'), 'glyphicon-comment',
                           None, login_required=True)
    frontpage.add_shortcut('xmpp', title, None, 'glyphicon-comment',
                           description, reverse_lazy('xmpp:index'),
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('ejabberd') and
            action_utils.webserver_is_enabled('jwchat-plinth'))


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def enable():
    """Enable the module."""
    actions.superuser_run('xmpp', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('xmpp', ['disable'])
    frontpage.remove_shortcut('jsxc')
    frontpage.remove_shortcut('xmpp')


def on_pre_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """
    Backup ejabberd database before hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['pre-change-hostname',
                           '--old-hostname', old_hostname,
                           '--new-hostname', new_hostname])


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """Update ejabberd config after hostname change."""
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-hostname',
                           '--old-hostname', old_hostname,
                           '--new-hostname', new_hostname],
                          async=True)


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Update ejabberd config after domain name change."""
    del sender  # Unused
    del old_domainname  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-domainname',
                           '--domainname', new_domainname],
                          async=True)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5222, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5222, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp6'))
    results.extend(
        action_utils.diagnose_url_on_all('http://{host}/http-bind/'))

    return results
