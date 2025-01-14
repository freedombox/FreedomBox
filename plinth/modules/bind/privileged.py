# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for BIND server."""

import pathlib
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
listen-on { !10.42.0.1; !10.42.1.1; !10.42.2.1; !10.42.3.1; !10.42.4.1; !10.42.5.1; !10.42.6.1; !10.42.7.1; any; };
directory "/var/cache/bind";

recursion yes;
allow-query { goodclients; };

forwarders {
127.0.0.53;
};
forward first;

auth-nxdomain no;    # conform to RFC1035
listen-on-v6 { any; };
};
'''  # noqa: E501
DEFAULT_FORWARDER = '127.0.0.53'  # systemd-resolved
LISTEN_ON = 'listen-on { !10.42.0.1; !10.42.1.1; !10.42.2.1; !10.42.3.1; '\
    '!10.42.4.1; !10.42.5.1; !10.42.6.1; !10.42.7.1; any; };'


@privileged
def setup(old_version: int):
    """Setup BIND configuration."""
    if old_version == 0:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as conf_file:
            conf_file.write(DEFAULT_CONFIG)
    elif old_version < 4:
        if not get_config()['forwarders']:
            _set_forwarders(DEFAULT_FORWARDER)

        if not _has_listen_on():
            _insert_listen_on()

        if old_version < 3:
            _remove_dnssec()

    Path(ZONES_DIR).mkdir(exist_ok=True, parents=True)

    action_utils.service_try_restart('named')


@privileged
def configure(forwarders: str):
    """Configure BIND."""
    _set_forwarders(forwarders)
    action_utils.service_try_restart('named')


def get_config():
    """Get current configuration."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r', encoding='utf-8')]

    forwarders = ''
    flag = False
    for line in data:
        if re.match(r'^\s*forwarders\s+{', line):
            flag = True
        elif flag and '//' not in line:
            forwarders = re.sub('[;]', '', line)
            flag = False

    return {'forwarders': forwarders}


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


def _remove_dnssec():
    """Remove DNSSEC options."""
    data = [line.strip() for line in open(CONFIG_FILE, 'r', encoding='utf-8')]

    with open(CONFIG_FILE, 'w', encoding='utf-8') as file_handle:
        for line in data:
            if not re.match(r'^\s*dnssec-enable\s+yes;', line):
                file_handle.write(line + '\n')


def _has_listen_on():
    """Return whether listen-on config option is present."""
    lines = pathlib.Path(CONFIG_FILE).read_text().splitlines()
    regex = r'^\s*listen-on\s+{'
    return any((re.match(regex, line) for line in lines))


def _insert_listen_on():
    """Insert the listen-on option."""
    config_file = pathlib.Path(CONFIG_FILE)
    lines = config_file.read_text().splitlines(keepends=True)
    write_lines = []
    for line in lines:
        write_lines += line
        if re.match(r'^\s*options\s+{', line):
            write_lines += LISTEN_ON + '\n'

    config_file.write_text(''.join(write_lines))


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
