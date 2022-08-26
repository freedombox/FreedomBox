# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for BIND server."""

import re
from collections import defaultdict
from pathlib import Path

import augeas

from plinth import action_utils
from plinth.actions import privileged

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


@privileged
def setup(old_version: int):
    """Setup BIND configuration."""
    if old_version == 0:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as conf_file:
            conf_file.write(DEFAULT_CONFIG)

    Path(ZONES_DIR).mkdir(exist_ok=True, parents=True)

    action_utils.service_restart('named')


@privileged
def configure(forwarders: str, dnssec: bool):
    """Configure BIND."""
    _set_forwarders(forwarders)
    _set_dnssec(dnssec)
    action_utils.service_restart('named')


def get_config():
    """Get current configuration."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r', encoding='utf-8')]

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


def _set_forwarders(forwarders):
    """Set DNS forwarders."""
    flag = 0
    data = [line.strip() for line in open(CONFIG_FILE, 'r', encoding='utf-8')]
    conf_file = open(CONFIG_FILE, 'w', encoding='utf-8')
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


def _set_dnssec(choice):
    """Enable or disable DNSSEC."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r', encoding='utf-8')]

    if choice:
        conf_file = open(CONFIG_FILE, 'w', encoding='utf-8')
        for line in data:
            if re.match(r'//\s*dnssec-enable\s+yes;', line):
                line = line.lstrip('/')
            conf_file.write(line + '\n')
        conf_file.close()
    else:
        conf_file = open(CONFIG_FILE, 'w', encoding='utf-8')
        for line in data:
            if re.match(r'^\s*dnssec-enable\s+yes;', line):
                line = '//' + line
            conf_file.write(line + '\n')
        conf_file.close()


def get_served_domains():
    """Return list of domains service handles.

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
