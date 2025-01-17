# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Names App."""

import pathlib
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged

fallback_conf = pathlib.Path(
    '/etc/systemd/resolved.conf.d/freedombox-fallback.conf')
override_conf = pathlib.Path('/etc/systemd/resolved.conf.d/freedombox.conf')
source_fallback_conf = pathlib.Path(
    '/usr/share/freedombox'
    '/etc/systemd/resolved.conf.d/freedombox-fallback.conf')

HOSTS_LOCAL_IP = '127.0.1.1'


@privileged
def set_hostname(hostname: str):
    """Set system hostname using hostnamectl."""
    subprocess.run(
        ['hostnamectl', 'set-hostname', '--transient', '--static', hostname],
        check=True)
    action_utils.service_restart('avahi-daemon')


def _load_augeas_hosts():
    """Initialize Augeas for editing /etc/hosts."""
    hosts_file = '/etc/hosts'
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('hosts', hosts_file)
    aug.set('/augeas/context', '/files' + hosts_file)
    aug.load()
    return aug


def get_domains(aug=None) -> list[str]:
    """Return the list of domains."""
    if not aug:
        aug = _load_augeas_hosts()

    domains = {}  # Maintain order of entries
    for match in aug.match('*'):
        if aug.get(match + '/ipaddr') != HOSTS_LOCAL_IP:
            continue

        domain = aug.get(match + '/canonical')
        aliases = []
        for alias_match in aug.match(match + '/alias'):
            aliases.append(aug.get(alias_match))

        # Read old style domains too.
        if aliases and '.' not in aliases[-1]:
            hostname = aliases[-1]
            if domain.startswith(hostname + '.'):
                domain = domain.partition('.')[2]
                aliases = aliases[:-1]

        for value in [domain] + aliases:
            if value:
                domains[domain] = True

    return list(domains.keys())


@privileged
def domain_add(domain_name: str | None = None):
    """Set system's static domain name in /etc/hosts."""
    aug = _load_augeas_hosts()
    domains = get_domains(aug)
    if domain_name in domains:
        return  # Domain already present in /etc/hosts

    aug.set('./01/ipaddr', HOSTS_LOCAL_IP)
    aug.set('./01/canonical', domain_name)
    aug.save()


@privileged
def domain_delete(domain_name: str | None = None):
    """Set system's static domain name in /etc/hosts."""
    aug = _load_augeas_hosts()
    domains = get_domains(aug)
    if domain_name not in domains:
        return  # Domain already not present in /etc/hosts

    for match in aug.match('*'):
        if aug.get(match + '/ipaddr') == HOSTS_LOCAL_IP and \
           aug.get(match + '/canonical') == domain_name:
            aug.remove(match)

    aug.save()


@privileged
def domains_migrate() -> None:
    """Convert old style of adding domain names to /etc/hosts to new.

    Old format:
        127.0.1.1 <hostname>.<domain> <hostname>

    New format:
        127.0.1.1 <domain1>
        127.0.1.1 <domain2>
    """
    aug = _load_augeas_hosts()
    domains = get_domains(aug)
    for match in aug.match('*'):
        if aug.get(match + '/ipaddr') == HOSTS_LOCAL_IP:
            aug.remove(match)

    for number, domain in enumerate(domains):
        aug.set(f'./0{number}/ipaddr', HOSTS_LOCAL_IP)
        aug.set(f'./0{number}/canonical', domain)

    aug.save()


@privileged
def install_resolved():
    """Install systemd-resolved related packages."""
    packages = ['systemd-resolved', 'libnss-resolve']
    subprocess.run(['dpkg', '--configure', '-a'], check=False)
    with action_utils.apt_hold_freedombox():
        action_utils.run_apt_command(['--fix-broken', 'install'])
        returncode = action_utils.run_apt_command(['install'] + packages)

    if returncode:
        raise RuntimeError(
            f'Apt command failed with return code: {returncode}')


@privileged
def set_resolved_configuration(dns_fallback: bool | None = None,
                               dns_over_tls: str | None = None,
                               dnssec: str | None = None):
    """Set systemd-resolved configuration options."""
    if dns_fallback is not None:
        _set_enable_dns_fallback(dns_fallback)

    if dns_over_tls is not None or dnssec is not None:
        _set_resolved_configuration(dns_over_tls, dnssec)

    # Workaround buggy reload that does not apply DNS-over-TLS changes
    # properly.
    action_utils.service_try_restart('systemd-resolved')


def get_resolved_configuration() -> dict[str, bool]:
    """Return systemd-resolved configuration."""
    configuration = _get_resolved_configuration()
    configuration['dns_fallback'] = fallback_conf.exists()
    return configuration


def _set_enable_dns_fallback(dns_fallback: bool):
    """Update whether to use DNS fallback servers."""
    if dns_fallback:
        if not fallback_conf.exists():
            fallback_conf.parent.mkdir(parents=True, exist_ok=True)
            fallback_conf.symlink_to(source_fallback_conf)
    else:
        fallback_conf.unlink(missing_ok=True)


def _load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Systemd', str(override_conf))
    aug.set('/augeas/context', '/files' + str(override_conf))
    aug.load()
    return aug


def _get_resolved_configuration():
    """Return overridden configuration for systemd-resolved."""
    aug = _load_augeas()
    # Default value for DNSSEC upstream is 'allow-downgrade', but in Debian it
    # is 'no'.
    return {
        'dns_over_tls': aug.get('Resolve/DNSOverTLS/value') or 'no',
        'dnssec': aug.get('Resolve/DNSSEC/value') or 'no'
    }


def _set_resolved_configuration(dns_over_tls: str | None = None,
                                dnssec: str | None = None):
    """Write configuration into a systemd-resolved override file."""
    aug = _load_augeas()

    if dns_over_tls is not None:
        aug.set('Resolve/DNSOverTLS/value', dns_over_tls)

    if dnssec is not None:
        aug.set('Resolve/DNSSEC/value', dnssec)

    aug.save()
