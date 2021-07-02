"""Configures spam filters and the virus scanner"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from plinth import actions

import plinth.modules.email_server.postconf as postconf

milter_config = {
    'milter_mail_macros': 'i {auth_type} {auth_authen} {auth_author} '\
    '{client_addr} {client_name} {mail_addr} {mail_host} {mail_mailer}',
    'smtpd_milters': 'inet:127.0.0.1:11332',
    'non_smtpd_milters': 'inet:127.0.0.1:11332'
}

logger = logging.getLogger(__name__)


def repair():
    logger.debug('Updating postconf: %r', milter_config)
    actions.superuser_run('email_server', ['-i', 'spam', 'set_filter'])


def action_set_filter():
    postconf.set_many(milter_config)
