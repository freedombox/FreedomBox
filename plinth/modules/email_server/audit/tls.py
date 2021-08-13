"""TLS configuration"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os

from plinth import actions

from . import models
from plinth.modules.email_server import interproc, postconf

# Mozilla Guideline v5.6, Postfix 1.17.7, OpenSSL 1.1.1d, intermediate
# Generated 2021-08
# https://ssl-config.mozilla.org/
tls_medium_cipherlist = [
    'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384', 'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-CHACHA20-POLY1305', 'ECDHE-RSA-CHACHA20-POLY1305',
    'DHE-RSA-AES128-GCM-SHA256', 'DHE-RSA-AES256-GCM-SHA384'
]

postfix_config = {
    # Enable TLS
    'smtpd_tls_security_level': 'may',
    'smtpd_tls_auth_only': 'yes',

    # Debugging information
    'smtpd_tls_received_header': 'yes',

    # Use a strong hashing algorithm
    'smtp_tls_fingerprint_digest': 'sha256',
    'smtpd_tls_fingerprint_digest': 'sha256',

    # Mozilla Intermediate Configuration
    'smtpd_tls_mandatory_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_protocols': '!SSLv2, !SSLv3, !TLSv1, !TLSv1.1',
    'smtpd_tls_mandatory_ciphers': 'medium',
    'tls_medium_cipherlist': ':'.join(tls_medium_cipherlist),
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

dovecot_cert_config = '/etc/dovecot/conf.d/91-freedombox-ssl.conf'

dovecot_cert_template = """# This file is managed by FreedomBox
ssl_cert = <{cert}
ssl_key = <{key}
"""

logger = logging.getLogger(__name__)


def get():
    results = []
    with postconf.mutex.lock_all():
        results.append(check_tls())
    return results


def repair():
    actions.superuser_run('email_server', ['-i', 'tls', 'set_up'])


def check_tls():
    diagnosis = models.MainCfDiagnosis('Postfix TLS')
    current = postconf.get_many_unsafe(list(postfix_config.keys()))
    diagnosis.compare_and_advise(current=current, default=postfix_config)
    return diagnosis


def repair_tls(diagnosis):
    diagnosis.assert_resolved()
    logger.info('Setting postconf: %r', diagnosis.advice)
    postconf.set_many_unsafe(diagnosis.advice)


def try_set_up_certificates():
    cert_folder = find_cert_folder()
    if not cert_folder:
        logger.warning('Could not find a suitable TLS certificate')
        return
    logger.info('Using TLS certificate in %s', cert_folder)

    cert = cert_folder + '/cert.pem'
    key = cert_folder + '/privkey.pem'
    write_postfix_cert_config(cert, key)
    write_dovecot_cert_config(cert, key)


def find_cert_folder() -> str:
    directory = '/etc/letsencrypt/live'
    domains_available = []
    for item in os.listdir(directory):
        if item[0] != '.' and os.path.isdir(directory + '/' + item):
            domains_available.append(item)
    domains_available.sort()

    if len(domains_available) == 0:
        return ''
    if len(domains_available) == 1:
        return directory + '/' + domains_available[0]
    # XXX Cannot handle the case with multiple domains
    if len(domains_available) > 1:
        return ''


def write_postfix_cert_config(cert, key):
    postconf.set_many_unsafe({
        'smtpd_tls_cert_file': cert,
        'smtpd_tls_key_file': key
    })


def write_dovecot_cert_config(cert, key):
    content = dovecot_cert_template.format(cert=cert, key=key)
    with interproc.atomically_rewrite(dovecot_cert_config) as fd:
        fd.write(content)


def action_set_up():
    with postconf.mutex.lock_all():
        repair_tls(check_tls())
        try_set_up_certificates()
