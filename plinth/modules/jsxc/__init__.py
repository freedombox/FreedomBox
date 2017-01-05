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
Plinth module to configure XMPP web client/jsxc
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

managed_packages = ['libjs-jsxc']

title = _('JSXC')

description = [

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
        service = service = service_module.Service(
            'jsxc', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
        if is_enabled():
            add_shortcut()


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
            'jsxc', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('jsxc', _('Chat Client \n (jsxc)'),
                           url=reverse_lazy('xmpp:jsxc'),
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('jwchat-plinth'))


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def enable():
    """Enable the module."""
    actions.superuser_run('jsxc', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('jsxc', ['disable'])
    frontpage.remove_shortcut('jsxc')
