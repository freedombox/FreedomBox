# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Generic HTTP request client for updating Dynamic DNS records.
"""

import subprocess
import urllib.parse
from typing import Any, Literal


def update(domain: dict[str, Any], ip_type: Literal['ipv4', 'ipv6'],
           external_address: str | None) -> str | None:
    """Update DNS entry using an update URL."""
    update_url = domain['update_url']
    quote = urllib.parse.quote
    if external_address:
        update_url = update_url.replace('<Ip>', quote(external_address))

    if domain['domain']:
        update_url = update_url.replace('<Domain>', quote(domain['domain']))

    if domain['username']:
        update_url = update_url.replace('<User>', quote(domain['username']))

    if domain['password']:
        update_url = update_url.replace('<Pass>', quote(domain['password']))

    options = ['-t', '3', '-T', '3']
    if domain['use_http_basic_auth']:
        options += [
            '--user', domain['username'], '--password', domain['password']
        ]

    if domain['disable_ssl_cert_check']:
        options += ['--no-check-certificate']

    if ip_type == 'ipv6':
        options += ['-6']
    else:
        options += ['-4']

    command = ['wget', '-O', '-'] + options + [update_url]
    subprocess.run(command, check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    return external_address
