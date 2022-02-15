"""Provides the diagnosis of SASL, mail submission, and user database lookup
configurations"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import plinth.modules.email.aliases as aliases
import plinth.modules.email.postconf as postconf
from plinth import actions

default_config = {
    'smtpd_sasl_auth_enable':
        'yes',
    'smtpd_sasl_type':
        'dovecot',
    'smtpd_sasl_path':
        'private/auth',
    'mailbox_transport':
        'lmtp:unix:private/dovecot-lmtp',
    'virtual_transport':
        'lmtp:unix:private/dovecot-lmtp',
    'smtpd_relay_restrictions':
        ','.join([
            'permit_sasl_authenticated',
            'defer_unauth_destination',
        ])
}

submission_flags = postconf.ServiceFlags(service='submission', type='inet',
                                         private='n', unpriv='-', chroot='y',
                                         wakeup='-', maxproc='-',
                                         command_args='smtpd')

default_submission_options = {
    'syslog_name': 'postfix/submission',
    'smtpd_tls_security_level': 'encrypt',
    'smtpd_client_restrictions': 'permit_sasl_authenticated,reject',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}

smtps_flags = postconf.ServiceFlags(service='smtps', type='inet', private='n',
                                    unpriv='-', chroot='y', wakeup='-',
                                    maxproc='-', command_args='smtpd')

default_smtps_options = {
    'syslog_name': 'postfix/smtps',
    'smtpd_tls_wrappermode': 'yes',
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}

SQLITE_ALIASES = 'sqlite:/etc/postfix/freedombox-aliases.cf'


def repair():
    """Tries to repair SASL, mail submission, and user lookup settings."""
    aliases.first_setup()
    actions.superuser_run('email', ['ldap', 'setup'])


def action_setup():
    postconf.set_many_unsafe(default_config)
    _setup_submission()
    _setup_alias_maps()


def _setup_submission():
    """Update configuration for smtps and smtp-submission."""
    postconf.set_master_cf_options(service_flags=submission_flags,
                                   options=default_submission_options)
    postconf.set_master_cf_options(service_flags=smtps_flags,
                                   options=default_smtps_options)


def _setup_alias_maps():
    """Setup alias maps to include an sqlite DB."""
    alias_maps = postconf.get_unsafe('alias_maps').replace(',', ' ').split(' ')
    if SQLITE_ALIASES not in alias_maps:
        alias_maps.append(SQLITE_ALIASES)

    postconf.set_many_unsafe({'alias_maps': ' '.join(alias_maps)})
