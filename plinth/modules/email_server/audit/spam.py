"""Configures spam filters and the virus scanner"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import subprocess

from plinth import actions

import plinth.modules.email_server.postconf as postconf
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
    'non_smtpd_milters': 'inet:127.0.0.1:11332'
}

logger = logging.getLogger(__name__)


def get():
    results = []
    with postconf.mutex.lock_all():
        results.append(check_filter())
    return results


def repair():
    actions.superuser_run('email_server', ['-i', 'spam', 'set_filter'])


def check_filter():
    diagnosis = models.MainCfDiagnosis('Postfix milter')
    current = postconf.get_many_unsafe(milter_config.keys())
    diagnosis.compare_and_advise(current=current, default=milter_config)
    return diagnosis


def fix_filter(diagnosis):
    diagnosis.assert_resolved()
    logger.info('Setting postconf: %r', diagnosis.advice)
    postconf.set_many_unsafe(diagnosis.advice)


def action_set_filter():
    with postconf.mutex.lock_all():
        fix_filter(check_filter())
    _compile_sieve()


def _compile_sieve():
    sieve_list = glob.glob('/etc/dovecot/freedombox-sieve-after/*.sieve')
    for sieve_file in sieve_list:
        _run_sievec(sieve_file)


def _run_sievec(sieve_file):
    logger.info('Compiling sieve script %s', sieve_file)
    args = ['sievec', '--', sieve_file]
    completed = subprocess.run(args, capture_output=True)
    if completed.returncode != 0:
        logger.critical('Subprocess returned %d', completed.returncode)
        logger.critical('Stdout: %r', completed.stdout)
        logger.critical('Stderr: %r', completed.stderr)
        raise OSError('Sieve compilation failed: ' + sieve_file)
