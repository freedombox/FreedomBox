"""Postconf wrapper providing thread-safe operations"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
import subprocess
import plinth.actions
from .lock import Mutex

postconf_mutex = Mutex('plinth-email-postconf.lock')


def get_many(key_list):
    """Acquire resource lock. Get the list of postconf values as specified.
    Return a key-value map"""
    result = {}
    with postconf_mutex.lock_all():
        for key in key_list:
            result[key] = get_no_lock(key)
        return result


def set_many(kv_map):
    """Acquire resource lock. Set the list of postconf values as specified"""
    # Encode email_server ipc input
    lines = []
    for key, value in kv_map.items():
        validate_key(key)
        validate_value(value)
        lines.append(key)
        lines.append(value)
    lines.append('\n')
    stdin = '\n'.join(lines).encode('utf-8')

    # Run action script as root
    args = ['ipc', 'postconf_set_many_v1']
    with postconf_mutex.lock_threads_only():
        # The action script will take care of file locking
        plinth.actions.superuser_run('email_server', args, input=stdin)


def get_no_lock(key):
    """Get postconf value (no locking)"""
    validate_key(key)
    result = _run(['/sbin/postconf', key])
    match = key + ' = '
    if not result.startswith(match):
        raise KeyError(key)
    return result[len(match):].strip()


def set_no_lock_assuming_root(key, value):
    """Set postconf value (assuming root and no locking)"""
    validate_key(key)
    validate_value(value)
    _run(['/sbin/postconf', '{}={}'.format(key, value)])


def _run(args):
    """Run process. Capture and return standard output as a string. Raise a
    RuntimeError on non-zero exit codes"""
    try:
        result = subprocess.run(args, check=True, capture_output=True)
        return result.stdout.decode('utf-8')
    except subprocess.SubprocessError as subprocess_error:
        raise RuntimeError('Subprocess failed') from subprocess_error
    except UnicodeDecodeError as unicode_error:
        raise RuntimeError('Unicode decoding failed') from unicode_error


def validate_key(key):
    """Validate postconf key format. Raises ValueError"""
    if not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', key):
        raise ValueError('Invalid postconf key format')


def validate_value(value):
    """Validate postconf value format. Raises ValueError"""
    for c in value:
        if ord(c) < 32:
            raise ValueError('Value contains control characters')
