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


@privileged
def set_hostname(hostname: str):
    """Set system hostname using hostnamectl."""
    subprocess.run(
        ['hostnamectl', 'set-hostname', '--transient', '--static', hostname],
        check=True)
    action_utils.service_restart('avahi-daemon')


@privileged
def set_domain_name(domain_name: str | None = None):
    """Set system's static domain name in /etc/hosts."""
    hostname = subprocess.check_output(['hostname']).decode().strip()
    hosts_path = pathlib.Path('/etc/hosts')
    if domain_name:
        insert_line = f'127.0.1.1 {hostname}.{domain_name} {hostname}\n'
    else:
        insert_line = f'127.0.1.1 {hostname}\n'

    lines = hosts_path.read_text(encoding='utf-8').splitlines(keepends=True)
    new_lines = []
    found = False
    for line in lines:
        if '127.0.1.1' in line:
            new_lines.append(insert_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(insert_line)

    hosts_path.write_text(''.join(new_lines), encoding='utf-8')


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
