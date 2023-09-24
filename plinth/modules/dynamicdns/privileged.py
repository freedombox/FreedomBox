# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Dynamic DNS."""

import pathlib
import urllib
from typing import Any

from plinth.actions import privileged

_conf_dir = pathlib.Path('/etc/ez-ipupdate/')
_active_config = _conf_dir / 'ez-ipupdate.conf'
_inactive_config = _conf_dir / 'ez-ipupdate.inactive'
_helper_config = _conf_dir / 'ez-ipupdate-plinth.cfg'
_cron_job = pathlib.Path('/etc/cron.d/ez-ipupdate')


def _read_configuration(path, separator='='):
    """Read ez-ipupdate configuration."""
    config = {}
    for line in path.read_text().splitlines():
        if line.startswith('#'):
            continue

        parts = line.partition(separator)
        if parts[1]:
            config[parts[0].strip()] = parts[2].strip()
        else:
            config[parts[0].strip()] = True

    return config


@privileged
def export_config() -> dict[str, bool | dict[str, dict[str, str | None]]]:
    """Return the old ez-ipupdate configuration in JSON format."""
    input_config = {}
    if _active_config.exists():
        input_config = _read_configuration(_active_config)
    elif _inactive_config.exists():
        input_config = _read_configuration(_inactive_config)

    helper = {}
    if _helper_config.exists():
        helper.update(_read_configuration(_helper_config, separator=' '))

    def _clean(value):
        value_map = {'enabled': True, 'disabled': False, '': None}
        return value_map.get(value, value)

    domain = {
        'service_type': 'gnudip',
        'domain': input_config.get('host'),
        'server': input_config.get('server'),
        'username': input_config.get('user', '').split(':')[0] or None,
        'password': input_config.get('user', '').split(':')[-1] or None,
        'ip_lookup_url': helper.get('IPURL'),
        'update_url': _clean(helper.get('POSTURL')) or None,
        'use_http_basic_auth': _clean(helper.get('POSTAUTH')),
        'disable_ssl_cert_check': _clean(helper.get('POSTSSLIGNORE')),
        'use_ipv6': _clean(helper.get('POSTUSEIPV6')),
    }

    if isinstance(domain['update_url'], bool):
        # 'POSTURL ' is a line found in the configuration file
        domain['update_url'] = None

    if not domain['server']:
        domain['service_type'] = 'other'
        update_url = domain['update_url']
        try:
            server = urllib.parse.urlparse(update_url).netloc
            service_types: dict[str, str] = {
                'dynupdate.noip.com': 'noip.com',
                'dynupdate.no-ip.com': 'noip.com',
                'freedns.afraid.org': 'freedns.afraid.org'
            }
            domain['service_type'] = service_types.get(str(server), 'other')
        except ValueError:
            pass

    # Old logic for 'enabling' the app is as follows: If behind NAT, add
    # cronjob. If not behind NAT and type is update URL, add cronjob. If not
    # behind NAT and type is GnuDIP, move inactive configuration to active
    # configuration and start the ez-ipupdate daemon.
    enabled = False
    if _cron_job.exists() or (domain['service_type'] == 'gnudip'
                              and _active_config.exists()):
        enabled = True

    output_config: dict[str, Any] = {'enabled': enabled, 'domains': {}}
    if domain['domain']:
        output_config['domains'][domain['domain']] = domain

    return output_config


@privileged
def clean():
    """Remove all old configuration files."""
    last_update = _conf_dir / 'last-update'
    status = _conf_dir / 'ez-ipupdate.status'
    current_ip = _conf_dir / 'ez-ipupdate.currentIP'

    cleanup_files = [
        _active_config, _inactive_config, last_update, _helper_config, status,
        current_ip
    ]
    for cleanup_file in cleanup_files:
        try:
            cleanup_file.rename(cleanup_file.with_suffix('.bak'))
        except FileNotFoundError:
            pass

    _cron_job.unlink(missing_ok=True)
