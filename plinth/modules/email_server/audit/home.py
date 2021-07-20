# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import os
import pwd
import subprocess

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from plinth.actions import superuser_run
from plinth.errors import ActionError

logger = logging.getLogger(__name__)


def exists_nam(username):
    """Returns True if the user's home directory exists"""
    try:
        passwd = pwd.getpwnam(username)
    except KeyError as e:
        raise ValidationError(_('User does not exist')) from e
    return _exists(passwd)


def exists_uid(uid_number):
    """Returns True if the user's home directory exists"""
    try:
        passwd = pwd.getpwuid(uid_number)
    except KeyError as e:
        raise ValidationError(_('User does not exist')) from e
    return _exists(passwd)


def _exists(passwd):
    return os.path.exists(passwd.pw_dir)


def put_nam(username):
    """Create a home directory for the user (identified by username)"""
    _put('nam', username)


def put_uid(uid_number):
    """Create a home directory for the user (identified by UID)"""
    _put('uid', str(uid_number))


def _put(arg_type, user_info):
    try:
        args = ['-i', 'home', 'mk', arg_type, user_info]
        superuser_run('email_server', args)
    except ActionError as e:
        raise RuntimeError('Action script failure') from e


def action_mk(arg_type, user_info):
    if arg_type == 'nam':
        passwd = pwd.getpwnam(user_info)
    elif arg_type == 'uid':
        passwd = pwd.getpwuid(int(user_info))
    else:
        raise ValueError('Unknown arg_type')

    args = ['sudo', '-n', '--user=#' + str(passwd.pw_uid)]
    args.extend(['/bin/sh', '-c', 'mkdir -p ~'])
    completed = subprocess.run(args, capture_output=True)
    if completed.returncode != 0:
        logger.critical('Subprocess returned %d', completed.returncode)
        logger.critical('Stdout: %r', completed.stdout)
        logger.critical('Stderr: %r', completed.stderr)
        raise OSError('Could not create home directory')
