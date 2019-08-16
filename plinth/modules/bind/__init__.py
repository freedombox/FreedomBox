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
FreedomBox app to configure BIND server.
"""

import re

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

name = _('BIND')

short_description = _('Domain Name Server')

managed_services = ['bind9']

managed_packages = ['bind9']

description = [
    _('BIND enables you to publish your Domain Name System (DNS) information '
      'on the Internet, and to resolve DNS queries for your user devices on '
      'your network.'),
    format_lazy(
        _('Currently, on {box_name}, BIND is only used to resolve DNS queries '
          'for other machines on local network. It is also incompatible with '
          'sharing Internet connection from {box_name}.'),
        box_name=_(cfg.box_name)),
]

port_forwarding_info = [
    ('TCP', 53),
    ('UDP', 53),
]

CONFIG_FILE = '/etc/bind/named.conf.options'

DEFAULT_CONFIG = '''
acl goodclients {
    localnets;
};
options {
directory "/var/cache/bind";

recursion yes;
allow-query { goodclients; };

forwarders {

};
forward first;

dnssec-enable yes;
dnssec-validation auto;

auth-nxdomain no;    # conform to RFC1035
listen-on-v6 { any; };
};
'''

app = None


class BindApp(app_module.App):
    """FreedomBox app for Bind."""

    app_id = 'bind'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-bind', name, short_description,
                              'fa-globe-w', 'bind:index',
                              parent_url_name='system')
        self.add(menu_item)

        firewall = Firewall('firewall-bind', name, ports=['dns'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-bind', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the BIND module."""
    global app
    app = BindApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'bind', ['setup'])
    helper.call('post', app.enable)


def force_upgrade(helper, _packages):
    """Force upgrade the managed packages to resolve conffile prompt."""
    helper.install(managed_packages, force_configuration='old')
    return True


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(53, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(53, 'udp6'))
    results.append(action_utils.diagnose_port_listening(53, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(53, 'udp4'))

    return results


def get_config():
    """Get current configuration"""
    data = [line.strip() for line in open(CONFIG_FILE, 'r')]

    forwarders = ''
    dnssec_enabled = False
    flag = False
    for line in data:
        if re.match(r'^\s*forwarders\s+{', line):
            flag = True
        elif re.match(r'^\s*dnssec-enable\s+yes;', line):
            dnssec_enabled = True
        elif flag and '//' not in line:
            forwarders = re.sub('[;]', '', line)
            flag = False

    conf = {
        'forwarders': forwarders,
        'enable_dnssec': dnssec_enabled,
    }
    return conf


def set_forwarders(forwarders):
    """Set DNS forwarders."""
    flag = 0
    data = [line.strip() for line in open(CONFIG_FILE, 'r')]
    conf_file = open(CONFIG_FILE, 'w')
    for line in data:
        if re.match(r'^\s*forwarders\s+{', line):
            conf_file.write(line + '\n')
            for dns in forwarders.split():
                conf_file.write(dns + '; ')
            conf_file.write('\n')
            flag = 1
        elif '};' in line and flag == 1:
            conf_file.write(line + '\n')
            flag = 0
        elif flag == 0:
            conf_file.write(line + '\n')
    conf_file.close()


def set_dnssec(choice):
    """Enable or disable DNSSEC."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r')]

    if choice == 'enable':
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'//\s*dnssec-enable\s+yes;', line):
                line = line.lstrip('/')
            conf_file.write(line + '\n')
        conf_file.close()

    if choice == 'disable':
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'^\s*dnssec-enable\s+yes;', line):
                line = '//' + line
            conf_file.write(line + '\n')
        conf_file.close()
