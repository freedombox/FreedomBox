"""Audit of LDAP and mail submission settings"""
# SPDX-License-Identifier: AGPL-3.0-or-later

from plinth import actions

import plinth.modules.email_server.postconf as postconf
from . import models

default_config = {
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_sasl_type': 'dovecot',
    'smtpd_sasl_path': 'private/auth'
}

submission_flags = postconf.ServiceFlags(
    service='submission', type='inet', private='n', unpriv='-', chroot='y',
    wakeup='-', maxproc='-', command_args='smtpd'
)

default_submission_options = {
    'syslog_name': 'postfix/submission',
    'smtpd_tls_security_level': 'encrypt',
    'smtpd_client_restrictions': 'permit_sasl_authenticated,reject',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}


def get():
    """Compare current values with the default. Generate an audit report

    Recommended endpoint name:
    GET /audit/ldap
    """
    results = models.Result('Postfix uses Dovecot for SASL authentication')
    current_config = postconf.get_many(list(default_config.keys()))
    for key, value in default_config.items():
        if current_config[key] != value:
            results.fails.append('{} should equal {}'.format(key, value))
    return [results]


def repair():
    """Tries to repair LDAP and mail submission settings

    Recommended endpoint name:
    POST /audit/ldap/repair
    """
    actions.superuser_run('email_server', ['ipc', 'set_sasl'])
    actions.superuser_run('email_server', ['ipc', 'set_submission'])


def action_set_sasl():
    """Called by email_server ipc set_sasl"""
    postconf.set_many(default_config)


def action_set_submission():
    """Called by email_server ipc set_submission"""
    postconf.set_master_cf_options(service_flags=submission_flags,
                                   options=default_submission_options)
