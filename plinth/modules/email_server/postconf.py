"""Postconf wrapper providing thread-safe operations"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import dataclasses
import re
import subprocess
import plinth.actions
from .lock import Mutex

postconf_mutex = Mutex('plinth-email-postconf.lock')


@dataclasses.dataclass
class ServiceFlags:
    service: str
    type: str
    private: str
    unpriv: str
    chroot: str
    wakeup: str
    maxproc: str
    command_args: str

    def serialize(self) -> str:
        return ' '.join([self.service, self.type, self.private, self.unpriv,
                         self.chroot, self.wakeup, self.maxproc,
                         self.command_args])


def get_many(key_list):
    """Acquire resource lock. Get the list of postconf values as specified.
    Return a key-value map"""
    result = {}
    for key in key_list:
        validate_key(key)
    with postconf_mutex.lock_all():
        for key in key_list:
            result[key] = get_unsafe(key)
        return result


def set_many(kv_map):
    """Acquire resource lock. Set the list of postconf values as specified"""
    for key, value in kv_map.items():
        validate_key(key)
        validate_value(value)

    with postconf_mutex.lock_all():
        for key, value in kv_map.items():
            set_unsafe(key, value)


def set_master_cf_options(service_flags, options):
    """Acquire resource lock. Set master.cf service options"""
    if not isinstance(service_flags, ServiceFlags):
        raise TypeError('service_flags')
    for key, value in options.items():
        validate_key(key)
        validate_value(value)

    service_slash_type = service_flags.service + '/' + service_flags.type
    flag_string = service_flags.serialize()

    with postconf_mutex.lock_all():
        # /sbin/postconf -M "service/type=flag_string"
        set_unsafe(service_slash_type, flag_string, '-M')
        for short_key, value in options.items():
            # /sbin/postconf -P "service/type/short_key=value"
            set_unsafe(service_slash_type + '/' + short_key, value, '-P')


def get_unsafe(key):
    """Get postconf value (no locking, no sanitization)"""
    result = _run(['/sbin/postconf', key])
    match = key + ' = '
    if not result.startswith(match):
        raise KeyError(key)
    return result[len(match):].strip()


def set_unsafe(key, value, flag=''):
    """Set postconf value (assuming root, no locking, no sanitization)"""
    if flag:
        _run(['/sbin/postconf', flag, '{}={}'.format(key, value)])
    else:
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
