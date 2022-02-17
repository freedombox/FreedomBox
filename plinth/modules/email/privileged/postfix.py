# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configure postfix to use auth and local delivery with dovecot. Start smtps and
submission services. Setup aliases database.
"""

from plinth import actions

from .. import aliases
from .. import postfix as postconf

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

submission_options = {
    'syslog_name': 'postfix/submission',
    'smtpd_tls_security_level': 'encrypt',
    'smtpd_client_restrictions': 'permit_sasl_authenticated,reject',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}
submission_service = postconf.Service(service='submission', type_='inet',
                                      private='n', unpriv='-', chroot='y',
                                      wakeup='-', maxproc='-', command='smtpd',
                                      options=submission_options)

smtps_options = {
    'syslog_name': 'postfix/smtps',
    'smtpd_tls_wrappermode': 'yes',
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_relay_restrictions': 'permit_sasl_authenticated,reject'
}
smtps_service = postconf.Service(service='smtps', type_='inet', private='n',
                                 unpriv='-', chroot='y', wakeup='-',
                                 maxproc='-', command='smtpd',
                                 options=smtps_options)

SQLITE_ALIASES = 'sqlite:/etc/postfix/freedombox-aliases.cf'


def setup():
    """Set SASL, mail submission, and user lookup settings."""
    aliases.first_setup()
    actions.superuser_run('email', ['postfix', 'setup'])


def action_setup():
    postconf.set_config(default_config)
    _setup_submission()
    _setup_alias_maps()


def _setup_submission():
    """Update configuration for smtps and smtp-submission."""
    postconf.set_master_config(submission_service)
    postconf.set_master_config(smtps_service)


def _setup_alias_maps():
    """Setup alias maps to include an sqlite DB."""
    alias_maps = postconf.get_config(['alias_maps'])['alias_maps']
    alias_maps = alias_maps.replace(',', ' ').split(' ')
    if SQLITE_ALIASES not in alias_maps:
        # Prioritize FreedomBox's sqlite based aliases file over /etc/aliases.
        # Otherwise, the common aliases will be pointing to 'root' instead of
        # first admin user (which is more practical in FreedomBox).
        alias_maps = [SQLITE_ALIASES] + alias_maps

    postconf.set_config({'alias_maps': ' '.join(alias_maps)})
