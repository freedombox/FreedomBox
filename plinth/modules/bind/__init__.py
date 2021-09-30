# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure BIND server.
"""

import re
from collections import defaultdict
from pathlib import Path

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from . import manifest

version = 2

managed_services = ['bind9', 'named']

managed_packages = ['bind9']

_description = [
    _('BIND enables you to publish your Domain Name System (DNS) information '
      'on the Internet, and to resolve DNS queries for your user devices on '
      'your network.'),
    format_lazy(
        _('Currently, on {box_name}, BIND is only used to resolve DNS queries '
          'for other machines on local network. It is also incompatible with '
          'sharing Internet connection from {box_name}.'),
        box_name=_(cfg.box_name)),
]

CONFIG_FILE = '/etc/bind/named.conf.options'
ZONES_DIR = '/var/bind/pri'

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
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('BIND'), icon='fa-globe-w',
                               short_description=_('Domain Name Server'),
                               description=_description)
        self.add(info)

        menu_item = menu.Menu('menu-bind', info.name, info.short_description,
                              info.icon, 'bind:index',
                              parent_url_name='system')
        self.add(menu_item)

        firewall = Firewall('firewall-bind', info.name, ports=['dns'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon(
            'daemon-bind', managed_services[0], listen_ports=[(53, 'tcp6'),
                                                              (53, 'udp6'),
                                                              (53, 'tcp4'),
                                                              (53, 'udp4')],
            alias=managed_services[1])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-bind',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call(
        'post', actions.superuser_run, 'bind',
        ['setup', '--old-version', str(old_version)])
    helper.call('post', app.enable)


def force_upgrade(helper, _packages):
    """Force upgrade the managed packages to resolve conffile prompt."""
    helper.install(managed_packages, force_configuration='old')
    return True


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


def get_served_domains():
    """

    Augeas path for zone files:
    ===========================
    augtool> print /files/var/bind/pri/local.zone
    /files/var/bind/pri/local.zone
    /files/var/bind/pri/local.zone/$TTL = "604800"
    /files/var/bind/pri/local.zone/@[1]
    /files/var/bind/pri/local.zone/@[1]/1
    /files/var/bind/pri/local.zone/@[1]/1/class = "IN"
    /files/var/bind/pri/local.zone/@[1]/1/type = "SOA"
    /files/var/bind/pri/local.zone/@[1]/1/mname = "localhost."
    /files/var/bind/pri/local.zone/@[1]/1/rname = "root.localhost."
    /files/var/bind/pri/local.zone/@[1]/1/serial = "2"
    /files/var/bind/pri/local.zone/@[1]/1/refresh = "604800"
    /files/var/bind/pri/local.zone/@[1]/1/retry = "86400"
    /files/var/bind/pri/local.zone/@[1]/1/expiry = "2419200"
    /files/var/bind/pri/local.zone/@[1]/1/minimum = "604800"
    /files/var/bind/pri/local.zone/@[2]
    /files/var/bind/pri/local.zone/@[2]/1
    /files/var/bind/pri/local.zone/@[2]/1/class = "IN"
    /files/var/bind/pri/local.zone/@[2]/1/type = "NS"
    /files/var/bind/pri/local.zone/@[2]/1/rdata = "localhost."
    /files/var/bind/pri/local.zone/@[3]
    /files/var/bind/pri/local.zone/@[3]/1
    /files/var/bind/pri/local.zone/@[3]/1/class = "IN"
    /files/var/bind/pri/local.zone/@[3]/1/type = "A"
    /files/var/bind/pri/local.zone/@[3]/1/rdata = "127.0.0.1"
    /files/var/bind/pri/local.zone/@[4]
    /files/var/bind/pri/local.zone/@[4]/1
    /files/var/bind/pri/local.zone/@[4]/1/class = "IN"
    /files/var/bind/pri/local.zone/@[4]/1/type = "AAAA"
    /files/var/bind/pri/local.zone/@[4]/1/rdata = "::1"

    Need to find the related functionality to parse the A records

    Retrieve from /etc/bind/db* zone files all the configured A records.
    Assuming zones files in ZONES_DIR are all used.
    :return: dictionary in the form 'domain_name': ['ip_address', 'ipv6_addr']
    """
    RECORD_TYPES = ('A', 'AAAA')
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Dns_Zone/lens', 'Dns_Zone.lns')

    zone_file_path = Path(ZONES_DIR)
    zone_files = [zf for zf in zone_file_path.iterdir() if zf.is_file()]

    # augeas load only required files
    for zone_file in zone_files:
        aug.set('/augeas/load/Dns_Zone/incl[last() + 1]', str(zone_file))

    aug.load()

    served_domains = defaultdict(list)
    for zone_file in zone_files:
        base_path = '/files/%s/@[{record_order}]/1/{field}' % zone_file
        count = 1
        mname = aug.get(base_path.format(record_order=count, field='mname'))
        while True:
            record_type = aug.get(
                base_path.format(record_order=count, field='type'))

            # no record type ends the search
            if record_type is None:
                break

            if record_type in RECORD_TYPES:
                served_domains[mname].append(
                    aug.get(base_path.format(record_order=count,
                                             field='rdata')))

            count += 1

    return served_domains
