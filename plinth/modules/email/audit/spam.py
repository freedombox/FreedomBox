"""Configures spam filters and the virus scanner"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess

from plinth import actions
from plinth.modules.email import postconf

_milter_config = {
    'smtpd_milters': 'inet:127.0.0.1:11332',
    'non_smtpd_milters': 'inet:127.0.0.1:11332',
}

def repair():
    actions.superuser_run('email', ['spam', 'set_filter'])


def action_set_filter():
    _compile_sieve()
    postconf.set_many(_milter_config)


def _compile_sieve():
    """Compile all .sieve script to binary format for performance."""
    sieve_dir = '/etc/dovecot/freedombox-sieve-after/'
    subprocess.run(['sievec', sieve_dir], check=True)
