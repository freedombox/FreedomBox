"""Audit of LDAP and mail submission settings"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from plinth import actions

import plinth.modules.email_server.postconf as postconf
from . import models

default_config = {
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_sasl_type': 'dovecot',
    'smtpd_sasl_path': 'private/auth',
    'mailbox_transport': 'lmtp:unix:private/dovecot-lmtp',
    'virtual_transport': 'lmtp:unix:private/dovecot-lmtp'
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

smtps_flags = postconf.ServiceFlags(
    service='smtps', type='inet', private='n', unpriv='-', chroot='y',
    wakeup='-', maxproc='-', command_args='smtpd'
)

default_smtps_options = {
    'syslog_name': 'postfix/smtps',
    'smtpd_tls_wrappermode': 'yes',
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}

logger = logging.getLogger(__name__)


def get():
    """Compare current values with the default. Generate an audit report

    Recommended endpoint name:
    GET /audit/ldap
    """
    results = []
    with postconf.postconf_mutex.lock_all():
        results.append(check_sasl())
    return results


def repair():
    """Tries to repair LDAP and mail submission settings

    Recommended endpoint name:
    POST /audit/ldap/repair
    """
    actions.superuser_run('email_server', ['-i', 'ldap', 'set_sasl'])
    actions.superuser_run('email_server', ['-i', 'ldap', 'set_submission'])


def check_sasl():
    diagnosis = models.MainCfDiagnosis('Postfix-Dovecot SASL integration')
    current = postconf.get_many_unsafe(default_config.keys())
    diagnosis.compare_and_advise(current=current, default=default_config)
    return diagnosis


def fix_sasl(diagnosis):
    diagnosis.assert_resolved()
    logger.info('Setting postconf: %r', diagnosis.advice)
    postconf.set_many_unsafe(diagnosis.advice)


def action_set_sasl():
    """Called by email_server ipc ldap set_sasl"""
    with postconf.postconf_mutex.lock_all():
        fix_sasl(check_sasl())


def action_set_submission():
    """Called by email_server ipc set_submission"""
    logger.info('Set postfix service: %r', default_submission_options)
    postconf.set_master_cf_options(service_flags=submission_flags,
                                   options=default_submission_options)

    logger.info('Set postfix service: %r', default_smtps_options)
    postconf.set_master_cf_options(service_flags=smtps_flags,
                                   options=default_smtps_options)
