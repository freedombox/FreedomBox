"""Provides the diagnosis of SASL, mail submission, and user database lookup
configurations"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.utils.translation import gettext_lazy as _

import plinth.modules.email_server.aliases as aliases
import plinth.modules.email_server.postconf as postconf
from plinth import actions

from . import models

default_config = {
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_sasl_type': 'dovecot',
    'smtpd_sasl_path': 'private/auth',
    'mailbox_transport': 'lmtp:unix:private/dovecot-lmtp',
    'virtual_transport': 'lmtp:unix:private/dovecot-lmtp',

    'smtpd_relay_restrictions': ','.join([
        'permit_sasl_authenticated', 'defer_unauth_destination',
    ])
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

MAILSRV_DIR = '/var/lib/plinth/mailsrv'
ETC_ALIASES = 'hash:/etc/aliases'
BEFORE_ALIASES = 'ldap:/etc/postfix/freedombox-username-to-uid-number.cf'
AFTER_ALIASES = 'hash:' + aliases.hash_db_path

logger = logging.getLogger(__name__)


def get():
    """Compare current values with the default. Generate an audit report

    Recommended endpoint name:
    GET /audit/ldap
    """
    translation_table = [
        (check_sasl, _('Postfix-Dovecot SASL integration')),
        (check_alias_maps, _('Postfix alias maps')),
        (check_local_recipient_maps, _('Postfix local recipient maps')),
    ]
    results = []
    with postconf.mutex.lock_all():
        for check, title in translation_table:
            results.append(check(title))
    return results


def repair():
    """Tries to repair SASL, mail submission, and user lookup settings

    Recommended endpoint name:
    POST /audit/ldap/repair
    """
    aliases.first_setup()
    actions.superuser_run('email_server', ['-i', 'ldap', 'set_up'])


def action_set_up():
    action_set_sasl()
    action_set_submission()
    action_set_ulookup()


def check_sasl(title=''):
    diagnosis = models.MainCfDiagnosis(title)
    diagnosis.compare(default_config, postconf.get_many_unsafe)
    return diagnosis


def fix_sasl(diagnosis):
    diagnosis.apply_changes(postconf.set_many_unsafe)


def action_set_sasl():
    """Handles email_server -i ldap set_sasl"""
    with postconf.mutex.lock_all():
        fix_sasl(check_sasl())


def action_set_submission():
    """Handles email_server -i ldap set_submission"""
    postconf.set_master_cf_options(service_flags=submission_flags,
                                   options=default_submission_options)
    postconf.set_master_cf_options(service_flags=smtps_flags,
                                   options=default_smtps_options)


def check_alias_maps(title=''):
    """Check the ability to mail to usernames and user aliases"""
    diagnosis = models.MainCfDiagnosis(title)

    analysis = models.AliasMapsAnalysis()
    analysis.parsed = postconf.parse_maps_by_key_unsafe('alias_maps')
    analysis.isystem = list_find(analysis.parsed, ETC_ALIASES)
    analysis.ibefore = list_find(analysis.parsed, BEFORE_ALIASES)
    analysis.iafter = list_find(analysis.parsed, AFTER_ALIASES)

    if analysis.ibefore == -1 or analysis.iafter == -1:
        diagnosis.flag_once('alias_maps', user=analysis)
        diagnosis.critical('Required maps not in list')
    if analysis.ibefore > analysis.iafter:
        diagnosis.flag_once('alias_maps', user=analysis)
        diagnosis.critical('Insecure map order')

    return diagnosis


def fix_alias_maps(diagnosis):
    diagnosis.repair('alias_maps', rearrange_alias_maps)
    diagnosis.apply_changes(postconf.set_many_unsafe)


def rearrange_alias_maps(analysis):
    # Delete *all* references to BEFORE_ALIASES and AFTER_ALIASES
    for i in range(len(analysis.parsed)):
        if analysis.parsed[i] in (BEFORE_ALIASES, AFTER_ALIASES):
            analysis.parsed[i] = ''
    # Does hash:/etc/aliases exist in list?
    if analysis.isystem >= 0:
        # Put the maps around hash:/etc/aliases
        val = '%s %s %s' % (BEFORE_ALIASES, ETC_ALIASES, AFTER_ALIASES)
        analysis.parsed[analysis.isystem] = val
    else:
        # To the end
        analysis.parsed.append(BEFORE_ALIASES)
        analysis.parsed.append(AFTER_ALIASES)
    # List -> string
    return ' '.join(filter(None, analysis.parsed))


def check_local_recipient_maps(title=''):
    diagnosis = models.MainCfDiagnosis(title)
    lrcpt_maps = postconf.parse_maps_by_key_unsafe('local_recipient_maps')
    list_modified = False

    # Block mails to system users
    # local_recipient_maps must not contain proxy:unix:passwd.byname
    ipasswd = list_find(lrcpt_maps, 'proxy:unix:passwd.byname')
    if ipasswd >= 0:
        diagnosis.critical('Mail to system users (/etc/passwd) possible')
        # Propose a fix
        lrcpt_maps[ipasswd] = ''
        list_modified = True

    if list_modified:
        fix = ' '.join(filter(None, lrcpt_maps))
        diagnosis.flag('local_recipient_maps', corrected_value=fix)

    return diagnosis


def fix_local_recipient_maps(diagnosis):
    diagnosis.apply_changes(postconf.set_many_unsafe)


def action_set_ulookup():
    """Handles email_server -i ldap set_ulookup"""
    with postconf.mutex.lock_all():
        fix_alias_maps(check_alias_maps())
        fix_local_recipient_maps(check_local_recipient_maps())


def list_find(lst, element, start=None, end=None):
    if start is None:
        start = 0
    if end is None:
        end = len(lst)
    if start < 0 or end < 0:
        return -1
    try:
        return lst.index(element, start, end)
    except ValueError:
        return -1
