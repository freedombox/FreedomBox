"""TLS configuration for postfix and dovecot."""
# SPDX-License-Identifier: AGPL-3.0-or-later

from plinth.modules.email_server import interproc, postconf

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
    # Enable TLS
    'smtpd_tls_security_level': 'may',

    # Allow unencrypted auth on port 25, needed by Roundcube
    'smtpd_tls_auth_only': 'no',

    # Debugging information
    'smtpd_tls_received_header': 'yes',

    # Use a strong hashing algorithm
    'smtp_tls_fingerprint_digest': 'sha256',
    'smtpd_tls_fingerprint_digest': 'sha256',

    # Mozilla Intermediate Configuration
    'smtpd_tls_mandatory_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_mandatory_ciphers': 'medium',
    'tls_medium_cipherlist': ':'.join(_tls_medium_cipherlist),
    'tls_preempt_cipherlist': 'no',

    # Postfix SMTP client
    'smtp_tls_mandatory_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtp_tls_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtp_tls_mandatory_ciphers': 'medium',

    # Use DNSSEC to validate TLS certificates
    'smtp_host_lookup': 'dns',
    'smtp_dns_support_level': 'dnssec',
    'smtp_tls_security_level': 'dane',  # Opportunistic DANE TLS

    # Maintain 1 cipherlist and keep it the most secure
    'tls_low_cipherlist': '$tls_medium_cipherlist',
    'tls_high_cipherlist': '$tls_medium_cipherlist',
}


def set_postfix_config(primary_domain, all_domains):
    """Set postfix configuration for TLS certificates."""
    tls_sni_map = '/etc/postfix/freedombox-tls-sni.map'
    config = dict(_postfix_config)
    config.update({
        'tls_server_sni_maps':
            tls_sni_map,
        'smtpd_tls_chain_files':
            f'/etc/postfix/letsencrypt/{primary_domain}/chain.pem'
    })
    postconf.set_many_unsafe(config)
    content = '# This file is managed by FreedomBox\n'
    for domain in all_domains:
        content += f'{domain} /etc/postfix/letsencrypt/{domain}/chain.pem\n'

    with interproc.atomically_rewrite(tls_sni_map) as file_handle:
        file_handle.write(content)


def set_dovecot_config(primary_domain, all_domains):
    """Set dovecot configuration for TLS certificates."""
    content = f'''# This file is managed by FreedomBox
ssl_cert = </etc/dovecot/letsencrypt/{primary_domain}/cert.pem
ssl_key = </etc/dovecot/letsencrypt/{primary_domain}/privkey.pem
'''
    for domain in all_domains:
        content += f'''
local_name {domain} {{
  ssl_cert = </etc/dovecot/letsencrypt/{domain}/cert.pem
  ssl_key = </etc/dovecot/letsencrypt/{domain}/privkey.pem
}}
'''
    dovecot_cert_config = '/etc/dovecot/conf.d/91-freedombox-tls.conf'
    with interproc.atomically_rewrite(dovecot_cert_config) as file_handle:
        file_handle.write(content)
