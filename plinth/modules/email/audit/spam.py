"""Configures spam filters and the virus scanner"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess

from plinth import actions
from plinth.modules.email import postconf

milter_config = {
    'milter_mail_macros':
        'i ' + ' '.join([
            '{auth_type}', '{auth_authen}', '{auth_author}', '{client_addr}',
            '{client_name}', '{mail_addr}', '{mail_host}', '{mail_mailer}'
        ]),
    # XXX In postconf this field is a list
    'smtpd_milters':
        'inet:127.0.0.1:11332',
    # XXX In postconf this field is a list
    'non_smtpd_milters':
        'inet:127.0.0.1:11332',
    'milter_header_checks':
        'regexp:fbx-managed/pre-queue-milter-headers',

    # Last-resort internal header cleanup at smtp client
    'smtp_header_checks':
        'regexp:/etc/postfix/freedombox-internal-cleanup',
}

# FreedomBox egress filtering

egress_filter = postconf.ServiceFlags(service='127.0.0.1:10025', type='inet',
                                      private='n', unpriv='-', chroot='y',
                                      wakeup='-', maxproc='-',
                                      command_args='smtpd')

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

egress_filter_cleanup = postconf.ServiceFlags(service='fbxcleanup',
                                              type='unix', private='n',
                                              unpriv='-', chroot='y',
                                              wakeup='-', maxproc='0',
                                              command_args='cleanup')

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

def repair():
    actions.superuser_run('email', ['spam', 'set_filter'])


def action_set_filter():
    _compile_sieve()
    postconf.set_master_cf_options(egress_filter, egress_filter_options)
    postconf.set_master_cf_options(egress_filter_cleanup,
                                   egress_filter_cleanup_options)

    postconf.set_many(milter_config)


def _compile_sieve():
    """Compile all .sieve script to binary format for performance."""
    sieve_dir = '/etc/dovecot/freedombox-sieve-after/'
    subprocess.run(['sievec', sieve_dir], check=True)
