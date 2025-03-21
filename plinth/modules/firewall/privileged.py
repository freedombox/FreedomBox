# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for FreedomBox firewall interface."""

import subprocess
from typing import TypeAlias

import augeas

from plinth import action_utils
from plinth.actions import privileged

FirewallConfig: TypeAlias = dict[str, str | list[str]]


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


def _run_firewall_cmd(args):
    """Run firewall-cmd command, discard output and check return value."""
    subprocess.run(['firewall-cmd'] + args, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)


def _setup_local_service_protection():
    """Create the basic set of direct rules for protecting local services.

    Local service protection means that only administrators and Apache web
    server should be able to access certain services and not other users who
    have logged into the system. This is needed because some of the services
    are protected with authentication and authorization provided by Apache web
    server. If services are contacted directly then auth can be bypassed by all
    local users.

    Firewalld does not have a mechanism to do this directly but it allows
    inserting 'direct' rules into firewall. nftables is our default backend by
    'direct' rules always invoke 'ip(6)tables' commands. Luckily, ip(6)tables
    are compatibility wrappers provided by nftables. Hence we must use iptables
    syntax even though we deal with nftables.

    In nftables, there is no direct way to write the blocking rules. To deal
    with traffic for incoming services, we have to write the rules an 'input'
    chain. However, this chain does not have the information about the user who
    originated this traffic. Only the 'output' chain has this information. This
    may be fixed in the future. See:
    https://github.com/firewalld/firewalld/issues/725

    Our workaround for the situation is to mark the packets in the 'output'
    chain and then use that wmark in the 'input'. Since we have a fixed set of
    users want to allow, a single bit in the 32bit 'mark' property of the
    packet is sufficient.
    """

    def _add_rule(permanent, *rule):
        try:
            _run_firewall_cmd(permanent + ['--direct', '--query-passthrough'] +
                              list(rule))
        except subprocess.CalledProcessError:
            _run_firewall_cmd(permanent + ['--direct', '--add-passthrough'] +
                              list(rule))

    for permanent in [[], ['--permanent']]:
        for ip_type in ['ipv4', 'ipv6']:
            for owner_type in ['--uid-owner', '--gid-owner']:
                for user_group in ['root', 'www-data', 'mail']:
                    _add_rule(permanent, ip_type, '-A', 'OUTPUT', '-m',
                              'owner', owner_type, user_group, '-j', 'MARK',
                              '--or-mark', '0x800000')

    for permanent in [[], ['--permanent']]:
        for ip_type in ['ipv4', 'ipv6']:
            _add_rule(permanent, ip_type, '-A', 'INPUT', '-m', 'conntrack',
                      '--ctstate', 'ESTABLISHED,RELATED', '-j', 'ACCEPT')
            _add_rule(permanent, ip_type, '-A', 'INPUT', '-m', 'mark',
                      '--mark', '0x800000/0x800000', '-j', 'ACCEPT')


def _setup_inter_zone_forwarding():
    """Create a new policy that allows forwarding between zones.

    https://bugzilla.redhat.com/show_bug.cgi?id=2016864#c8
    """

    def _run(args):
        """Run a firewall command with --permanent argument."""
        return _run_firewall_cmd(['--permanent'] + args)

    policy_name = 'fbx_int_to_ext_fwd'
    try:
        _run(['--new-policy', policy_name])
    except subprocess.CalledProcessError as exception:
        if exception.returncode != 26:  # NAME_CONFLICT
            raise

    _run(['--policy', policy_name, '--add-ingress-zone', 'internal'])
    _run(['--policy', policy_name, '--add-egress-zone', 'external'])
    _run(['--policy', policy_name, '--set-priority', '100'])
    _run(['--policy', policy_name, '--set-target', 'ACCEPT'])

    # Enable masquerade on external zone
    _run(['--zone=external', '--add-masquerade'])

    # Enable intra-zone forwarding on internal zone
    _run(['--zone=internal', '--add-forward'])

    # Restart firewalld
    action_utils.service_reload('firewalld')


@privileged
def setup():
    """Perform basic firewalld setup."""
    action_utils.service_enable('firewalld')
    subprocess.run(['firewall-cmd', '--set-default-zone=external'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=True)
    set_firewall_backend('nftables')

    _setup_local_service_protection()

    _setup_inter_zone_forwarding()


@privileged
def get_config() -> FirewallConfig:
    """Return firewalld configuration for diagnostics."""
    config: FirewallConfig = {}

    # Get the default zone.
    output = subprocess.check_output(['firewall-cmd', '--get-default-zone'])
    config['default_zone'] = output.decode().strip()

    # Load Augeas lens.
    conf_file = '/etc/firewalld/firewalld.conf'
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Shellvars', conf_file)
    aug.set('/augeas/context', '/files' + conf_file)
    aug.load()

    # Get the firewall backend.
    config['backend'] = aug.get('FirewallBackend')

    # Get the list of direct passthroughs.
    output = subprocess.check_output(
        ['firewall-cmd', '--direct', '--get-all-passthroughs'])
    config['passthroughs'] = output.decode().strip().split('\n')

    return config
