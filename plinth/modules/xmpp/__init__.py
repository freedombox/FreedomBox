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

from gettext import gettext as _
import json

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change


depends = ['plinth.modules.apps']

service = None


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Chat Server (XMPP)'), 'glyphicon-comment',
                     'xmpp:index', 400)

    global service
    service = service_module.Service(
        'xmpp', _('Chat Server (XMPP)'),
        ['xmpp-client', 'xmpp-server', 'xmpp-bosh'],
        is_external=True, enabled=is_enabled())

    pre_hostname_change.connect(on_pre_hostname_change)
    post_hostname_change.connect(on_post_hostname_change)
    domainname_change.connect(on_domainname_change)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('ejabberd') and
            action_utils.webserver_is_enabled('jwchat-plinth'))


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('ejabberd')


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


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5222, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5222, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5269, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5280, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all('http://{host}/jwchat'))

    return results
