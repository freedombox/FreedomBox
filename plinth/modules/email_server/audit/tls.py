"""TLS configuration"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import logging
import os
import sys

from django.utils.translation import ugettext_lazy as _
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
    _get_regular_results(results)
    _get_superuser_results(results)
    return results


def _get_regular_results(results):
    translation_table = [
        (check_tls, _('Postfix TLS parameters')),
        (check_postfix_cert_usage, _('Postfix uses a TLS certificate')),
    ]
    with postconf.mutex.lock_all():
        for check, title in translation_table:
            results.append(check(title))


def _get_superuser_results(results):
    translation = {
        'cert_availability': _('Has a TLS certificate'),
    }
    dump = actions.superuser_run('email_server', ['-i', 'tls', 'check'])
    for jmap in json.loads(dump):
        results.append(models.Diagnosis.from_json(jmap, translation.get))


def repair():
    actions.superuser_run('email_server', ['-i', 'tls', 'set_up'])


def repair_component(action):
    action_to_services = {'set_cert': ['dovecot', 'postfix']}
    if action not in action_to_services:  # action not allowed
        return
    actions.superuser_run('email_server', ['-i', 'tls', action])
    return action_to_services[action]


def check_tls(title=''):
    diagnosis = models.MainCfDiagnosis(title)
    diagnosis.compare(postfix_config, postconf.get_many_unsafe)
    return diagnosis


def repair_tls(diagnosis):
    diagnosis.apply_changes(postconf.set_many_unsafe)


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
    try:
        listdir_result = os.listdir(directory)
    except OSError:
        return ''

    for item in listdir_result:
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


def check_postfix_cert_usage(title=''):
    prefix = '/etc/letsencrypt/live/'
    diagnosis = models.Diagnosis(title, action='set_cert')
    conf = postconf.get_many_unsafe(['smtpd_tls_cert_file',
                                     'smtpd_tls_key_file'])
    if not conf['smtpd_tls_cert_file'].startswith(prefix):
        diagnosis.error("Cert file not in Let's Encrypt directory")
    if not conf['smtpd_tls_key_file'].startswith(prefix):
        diagnosis.error("Privkey file not in Let's Encrypt directory")

    return diagnosis


def su_check_cert_availability(title=''):
    diagnosis = models.Diagnosis(title)
    if find_cert_folder() == '':
        diagnosis.error("Could not find a Let's Encrypt certificate")
    return diagnosis


def action_set_up():
    with postconf.mutex.lock_all():
        repair_tls(check_tls())
        try_set_up_certificates()


def action_set_cert():
    with postconf.mutex.lock_all():
        try_set_up_certificates()


def action_check():
    checks = ('cert_availability',)
    results = []
    for check_name in checks:
        check_function = globals()['su_check_' + check_name]
        results.append(check_function(check_name).to_json())
    json.dump(results, sys.stdout, indent=0)  # indent=0 adds a new line
