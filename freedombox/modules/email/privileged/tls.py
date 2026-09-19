# SPDX-License-Identifier: AGPL-3.0-or-later
"""
TLS certificate configuration for postfix and dovecot.

See: https://ssl-config.mozilla.org/
See: http://www.postfix.org/TLS_README.html
See: https://doc.dovecot.org/configuration_manual/dovecot_ssl_configuration/
"""

import pathlib

from .. import postfix
from ..dovecot import is_version_24

# Mozilla Guideline v5.6, Postfix 1.17.7, OpenSSL 1.1.1d, intermediate
# Generated 2021-08
# https://ssl-config.mozilla.org/
_tls_medium_cipherlist = [
    'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384', 'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-CHACHA20-POLY1305', 'ECDHE-RSA-CHACHA20-POLY1305',
    'DHE-RSA-AES128-GCM-SHA256', 'DHE-RSA-AES256-GCM-SHA384'
]

_postfix_config = {
    # Allow unencrypted auth on port 25, needed by Roundcube
    'smtpd_tls_auth_only': 'no',

    # Mozilla Intermediate Configuration
    'smtpd_tls_security_level': 'may',
    'smtpd_tls_mandatory_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_mandatory_ciphers': 'medium',
    'smtpd_tls_ciphers': 'medium',
    'tls_medium_cipherlist': ':'.join(_tls_medium_cipherlist),
    'tls_preempt_cipherlist': 'no',

    # Postfix SMTP client
    'smtp_tls_mandatory_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtp_tls_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtp_tls_mandatory_ciphers': 'medium',
    'smtp_tls_ciphers': 'medium',

    # Use DNSSEC to validate TLS certificates
    'smtp_host_lookup': 'dns',
    'smtp_dns_support_level': 'dnssec',
    'smtp_tls_security_level': 'dane',  # Opportunistic DANE TLS
}


def set_postfix_config(primary_domain, all_domains):
    """Set postfix configuration for TLS certificates."""
    items = []
    for domain in all_domains:
        items.append(f'{domain}=/etc/postfix/letsencrypt/{domain}/chain.pem')

    domain_map = ','.join(items)
    config = dict(_postfix_config)
    config.update({
        'tls_server_sni_maps':
            f'inline:{{{domain_map}}}',
        'smtpd_tls_chain_files':
            f'/etc/postfix/letsencrypt/{primary_domain}/chain.pem',
        'smtpd_tls_cert_file':
            ''
    })
    postfix.set_config(config)


def set_dovecot_config(primary_domain, all_domains):
    """Set dovecot configuration for TLS certificates."""
    is_new_version = is_version_24()

    # Determine whether to prefix file paths with '<' based on version
    prefix = ''
    cert_naming = 'ssl_server_cert_file'
    key_naming = 'ssl_server_key_file'
    if not is_new_version:
        prefix = '<'
        cert_naming = 'ssl_cert'
        key_naming = 'ssl_key'

    content = f'''# This file is managed by FreedomBox
{cert_naming} = {prefix}/etc/dovecot/letsencrypt/{primary_domain}/cert.pem
{key_naming} = {prefix}/etc/dovecot/letsencrypt/{primary_domain}/privkey.pem
'''

    for domain in all_domains:
        content += f'''
local_name {domain} {{
  {cert_naming} = {prefix}/etc/dovecot/letsencrypt/{domain}/cert.pem
  {key_naming} = {prefix}/etc/dovecot/letsencrypt/{domain}/privkey.pem
}}
'''
    cert_config = pathlib.Path('/etc/dovecot/conf.d/91-freedombox-tls.conf')
    cert_config.write_text(content, encoding='utf-8')
