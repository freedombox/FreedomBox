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

import re

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import service as service_module
from plinth.menu import main_menu

version = 1

name = _('BIND')

short_description = _('Domain Name Server')

service = None

managed_services = ['bind9']

managed_packages = ['bind9']

description = [
    _('BIND enables you to publish your Domain Name System (DNS) information '
      'on the Internet, and to resolve DNS queries for your user devices on '
      'your network.')
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
8.8.8.8; 8.8.4.4;
};
forward first;

dnssec-enable yes;
dnssec-validation auto;

auth-nxdomain no;    # conform to RFC1035
listen-on-v6 { any; };
};
'''


def init():
    """Intialize the BIND module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-globe', 'bind:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name,
                                         ports=['dns'], is_external=False)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name,
                                         ports=['dns'], is_external=True,
                                         enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', actions.superuser_run, 'bind', ['setup'])


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])


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

    forwarding_enabled = False
    dnssec_enabled = False
    forwarders = ''
    flag = False
    for line in data:
        if re.match(r'^\s*forwarders\s+{', line):
            forwarding_enabled = True
            flag = True
        elif re.match(r'^\s*dnssec-enable\s+yes;', line):
            dnssec_enabled = True
        elif flag and '//' not in line:
            forwarders = re.sub('[;]', '', line)
            flag = False

    conf = {
        'set_forwarding': forwarding_enabled,
        'enable_dnssec': dnssec_enabled,
        'forwarders': forwarders
    }
    return conf


def set_forwarding(choice):
    """Enable or disable DNS forwarding."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r')]
    flag = 0
    if choice == "false":
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'^\s*forwarders\s+{', line):
                flag = 1
            if flag == 1:
                line = '// ' + line
            if re.match(r'forward\s+first', line):
                flag = 0
            conf_file.write(line + '\n')
        conf_file.close()

    else:
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'//\s*forwarders\s+{', line):
                flag = 1
            if flag == 1:
                line = line.lstrip('/')
            if re.match(r'forward\s+first', line):
                flag = 0
            conf_file.write(line + '\n')
        conf_file.close()


def enable_dnssec(choice):
    """Enable or disable DNSSEC."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r')]
    if choice == "false":
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'^\s*dnssec-enable\s+yes;', line):
                line = '//' + line
            conf_file.write(line + '\n')
        conf_file.close()

    else:
        conf_file = open(CONFIG_FILE, 'w')
        for line in data:
            if re.match(r'//\s*dnssec-enable\s+yes;', line):
                line = line.lstrip('/')
            conf_file.write(line + '\n')
        conf_file.close()


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
