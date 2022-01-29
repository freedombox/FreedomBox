"""Configures spam filters and the virus scanner"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import re
import subprocess

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth.modules.email import interproc, lock, postconf
from plinth.modules.email.modconf import ConfigInjector

from . import models

milter_config = {
    'milter_mail_macros': 'i ' + ' '.join([
        '{auth_type}', '{auth_authen}', '{auth_author}',
        '{client_addr}', '{client_name}',
        '{mail_addr}', '{mail_host}', '{mail_mailer}'
    ]),
    # XXX In postconf this field is a list
    'smtpd_milters': 'inet:127.0.0.1:11332',
    # XXX In postconf this field is a list
    'non_smtpd_milters': 'inet:127.0.0.1:11332',
    'milter_header_checks': 'regexp:fbx-managed/pre-queue-milter-headers',

    # Last-resort internal header cleanup at smtp client
    'smtp_header_checks': 'regexp:/etc/postfix/freedombox-internal-cleanup',
    # Reserved mail transports
    # XXX This field is a list
    'transport_maps': 'regexp:/etc/postfix/freedombox-transport-to',
    # XXX This field is a list
    'sender_dependent_default_transport_maps': \
    'regexp:/etc/postfix/freedombox-transport-from',
}

# FreedomBox egress filtering

egress_filter = postconf.ServiceFlags(
    service='127.0.0.1:10025', type='inet', private='n', unpriv='-',
    chroot='y', wakeup='-', maxproc='-', command_args='smtpd'
)

egress_filter_options = {
    'syslog_name': 'postfix/fbxout',
    'cleanup_service_name': 'fbxcleanup',
    'content_filter': '',
    'receive_override_options': 'no_unknown_recipient_checks',
    'smtpd_helo_restrictions': '',
    'smtpd_client_restrictions': '',
    'smtpd_relay_restrictions': '',
    'smtpd_recipient_restrictions': 'permit_mynetworks,reject',
    'mynetworks': '127.0.0.0/8,[::1]/128'
}

egress_filter_cleanup = postconf.ServiceFlags(
    service='fbxcleanup', type='unix', private='n', unpriv='-',
    chroot='y', wakeup='-', maxproc='0', command_args='cleanup'
)

egress_filter_cleanup_options = {
    'syslog_name': 'postfix/fbxout',
    # "From" domain rewriting
    'sender_canonical_maps': 'regexp:/etc/postfix/freedombox-rewrite-sender',
    'local_header_rewrite_clients': 'static:all',
    # "From" domain masquerading
    'masquerade_domains': '$mydomain',
    'masquerade_classes': 'envelope_sender,header_sender',
    # Header privacy
    'header_checks': 'regexp:/etc/postfix/freedombox-header-cleanup',
    'nested_header_checks': ''
}

# Rspamd config

rspamd_re = re.compile('#[ ]*--[ ]*([A-Z]{3,5})[ ]+FREEDOMBOX CONFIG$')
rspamd_format = '#-- {} FREEDOMBOX CONFIG'

rspamd_mutex = lock.Mutex('rspamd-config')
logger = logging.getLogger(__name__)


def get():
    translation_table = [
        (check_filter, _('Inbound and outbound mail filters')),
    ]
    results = []
    with postconf.mutex.lock_all():
        for check, title in translation_table:
            results.append(check(title))
    return results


def repair():
    actions.superuser_run('email', ['spam', 'set_filter'])


def check_filter(title=''):
    diagnosis = models.MainCfDiagnosis(title)
    diagnosis.compare(milter_config, postconf.get_many_unsafe)
    return diagnosis


def fix_filter(diagnosis):
    diagnosis.apply_changes(postconf.set_many_unsafe)


def action_set_filter():
    _compile_sieve()
    postconf.set_master_cf_options(egress_filter, egress_filter_options)
    postconf.set_master_cf_options(egress_filter_cleanup,
                                   egress_filter_cleanup_options)

    with postconf.mutex.lock_all():
        fix_filter(check_filter())

    injector = ConfigInjector(rspamd_re, rspamd_format)
    with rspamd_mutex.lock_all():
        # XXX Maybe use globbing?
        _inject_rspamd_config(injector, 'override', 'options.inc')
        _inject_rspamd_config(injector, 'local', 'milter_headers.conf')


def _inject_rspamd_config(injector, type, name):
    template_path = '/etc/plinth/rspamd-config/%s_%s' % (type, name)
    config_path = '/etc/rspamd/%s.d/%s' % (type, name)

    logger.info('Opening Rspamd config file %s', config_path)
    injector.do_template_file(template_path, config_path)


def _compile_sieve():
    sieve_list = glob.glob('/etc/dovecot/freedombox-sieve-after/*.sieve')
    for sieve_file in sieve_list:
        _run_sievec(sieve_file)


def _run_sievec(sieve_file):
    logger.info('Compiling sieve script %s', sieve_file)
    args = ['sievec', '--', sieve_file]
    completed = subprocess.run(args, capture_output=True, check=False)
    if completed.returncode != 0:
        interproc.log_subprocess(completed)
        raise OSError('Sieve compilation failed: ' + sieve_file)
