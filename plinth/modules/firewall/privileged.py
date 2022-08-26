# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for FreedomBox firewall interface."""

import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged


def _flush_iptables_rules():
    """Flush firewalld iptables rules before restarting it.

    This is workaround for
    https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=914694

    This workaround can be removed if the bug is fixed or if firewalld starts
    defaulting to nftables again.

    The bug leads to firewalld failing to flush rules when there are custom
    chains in the rules. This only happens on firewalld iptables backend when
    nftables is running with iptables compatibility.

    Flushing the tables before a restart will make the restart succeed and
    after the restart nftables backend is used avoiding the problem.

    """
    rule_template = '*{table}\n-F\n-X\n-Z\nCOMMIT\n'
    iptables_rules = ''
    ip6tables_rules = ''
    for table in ['security', 'raw', 'mangle', 'nat', 'filter']:
        iptables_rules += rule_template.format(table=table)
        ip6tables_rules += rule_template.format(table=table)

    subprocess.run(['iptables-restore'], input=iptables_rules.encode(),
                   check=True)
    subprocess.run(['ip6tables-restore'], input=iptables_rules.encode(),
                   check=True)


def set_firewall_backend(backend):
    """Set FirewallBackend attribute to the specified string."""
    conf_file = '/etc/firewalld/firewalld.conf'
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

    # lens for shell-script config file
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', conf_file)
    aug.load()

    old_backend = aug.get('/files/{}/FirewallBackend'.format(conf_file))
    aug.set('/files/{}/FirewallBackend'.format(conf_file),
            '{}'.format(backend))
    aug.save()

    if old_backend == 'iptables':
        _flush_iptables_rules()

    if backend != old_backend:
        action_utils.service_restart('firewalld')


@privileged
def setup():
    """Perform basic firewalld setup."""
    action_utils.service_enable('firewalld')
    subprocess.run(['firewall-cmd', '--set-default-zone=external'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=True)
    set_firewall_backend('nftables')
