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

from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu


version = 1

managed_packages = ['libjs-jsxc']

title = _('Chat Client \n (JSXC)')

description = [

    _('JSXC is a web client for XMPP. Typically it is used with an XMPP '
      'server running locally.'),
]

service = None

logger = logging.getLogger(__name__)


def init():
    """Initialize the JSXC module"""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-comment', 'jsxc:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'jsxc', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    global service
    if not service:
        service = service_module.Service(
            'jsxc', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('jsxc', _('Chat Client \n (jsxc)'),
                           url=reverse_lazy('jsxc:jsxc'),
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    setup_helper = globals()['setup_helper']
    return setup_helper.get_state() != 'needs-setup'


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def enable():
    add_shortcut()


def disable():
    frontpage.remove_shortcut('jsxc')
