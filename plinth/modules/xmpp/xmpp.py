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

from django import forms
from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging
import socket

from plinth import actions
from plinth import cfg
from plinth import package
from plinth import service
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change


logger = logging.getLogger(__name__)


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('XMPP', 'glyphicon-comment', 'xmpp:index', 40)

    service.Service(
        'xmpp-client', _('Chat Server - client connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-server', _('Chat Server - server connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
        enabled=True)

    pre_hostname_change.connect(on_pre_hostname_change)
    post_hostname_change.connect(on_post_hostname_change)
    domainname_change.connect(on_domainname_change)


def before_install():
    """Preseed debconf values before the packages are installed."""
    fqdn = socket.getfqdn()
    domainname = '.'.join(fqdn.split('.')[1:])
    logger.info('XMPP service domainname - %s', domainname)
    actions.superuser_run('xmpp', ['pre-install', '--domainname', domainname])


def on_install():
    """Setup jwchat apache conf"""
    actions.superuser_run('xmpp', ['setup'])


@package.required(['jwchat', 'ejabberd'],
                  before_install=before_install,
                  on_install=on_install)
def index(request):
    """Serve XMPP page"""
    return TemplateResponse(request, 'xmpp.html',
                            {'title': _('XMPP Server')})


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
    """
    Update ejabberd and jwchat config after hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-hostname',
                           '--old-hostname', old_hostname,
                           '--new-hostname', new_hostname],
                          async=True)


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """
    Update ejabberd and jwchat config after domain name is changed.
    """
    del sender  # Unused
    del old_domainname  # Unused
    del kwargs  # Unused

    actions.superuser_run('xmpp',
                          ['change-domainname',
                           '--domainname', new_domainname],
                          async=True)
