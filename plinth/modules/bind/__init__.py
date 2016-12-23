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
Plinth module to configure BIND server
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.views import ServiceView


version = 1

depends = ['apps']

title = _('Domain Name Server \n (BIND)')

service = None

managed_services = ['bind9']

managed_packages = ['bind9', 'bind9utils', 'bind9-doc']

description = [
    _('BIND is open source software that enables you to publish your Domain '
      'Name System (DNS) information on the Internet, and to resolve '
      'DNS queries for your users.'),

    _('BIND is by far the most widely used DNS software on the Internet, '
      'providing a robust and stable platform on top of which organizations'
      ' can build distributed computing systems with the knowledge that those '
      'systems are fully compliant with published DNS standards.')
]

CONFIG_FILE = '/etc/bind/named.conf.options'

value1 = 'acl goodclients { \n   localhost;\n};\n'
value2 = '        recursion yes;\n           allow-query { goodclients; };\n\n'
value3 = '	// 	8.8.8.8;\n	// 	8.8.4.4;\n'


def init():
    """Intialize the BIND module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(title, 'glyphicon-globe', 'bind:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['bind-plinth'],
            is_external=True,
            )


class BindServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "bind"
    description = description


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['bind-plinth'],
            is_external=True,
            enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', default_config)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('bind')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(53, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(53, 'udp6'))

    return results

def default_config():
    """Initialize config file for BIND"""
    f = open(CONFIG_FILE, "r")
    contents = f.readlines()
    f.close()

    contents.insert(0, value1)
    contents.insert(4, value2)
    contents.insert(15, value3)

    f = open(CONFIG_FILE, "w")
    contents = "".join(contents)
    f.write(contents)
    f.close()

def get_default():
    """Get initial value for forwarding"""
    f = open(CONFIG_FILE, "r")
    contents = f.readlines()
    if '// forwarders {' in contents:
        conf = {
            'set_forwarding': False}
    else:
        conf = {
            'set_forwarding': True}
