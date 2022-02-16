"""Postconf wrapper providing thread-safe operations"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import re
import subprocess
from dataclasses import dataclass
from typing import ClassVar

from . import interproc

logger = logging.getLogger(__name__)


@dataclass
class ServiceFlags:
    service: str
    type: str
    private: str
    unpriv: str
    chroot: str
    wakeup: str
    maxproc: str
    command_args: str

    crash_handler: ClassVar[str] = '/dev/null/plinth-crash'

    def _get_flags_ordered(self):
        return [
            self.service, self.type, self.private, self.unpriv, self.chroot,
            self.wakeup, self.maxproc, self.command_args
        ]

    def serialize(self) -> str:
        ordered = self._get_flags_ordered()
        return ' '.join(ordered)

    def serialize_temp(self) -> str:
        ordered = self._get_flags_ordered()
        ordered[-1] = self.crash_handler
        return ' '.join(ordered)

    def try_remove_crash_handler(self, line) -> str:
        pattern = re.compile('([^ \\t]+)[ \\t]+([a-z]+)[ \\t]+')
        match = pattern.match(line)
        if match is None:
            return None
        if match.group(1) != self.service or match.group(2) != self.type:
            return None
        if not line.rstrip().endswith(self.crash_handler):
            return None
        return line.replace(self.crash_handler, self.command_args)


def get_many(key_list):
    """Acquire resource lock. Get the list of postconf values as specified.
    Return a key-value map"""
    for key in key_list:
        validate_key(key)

    return get_many_unsafe(key_list)


def get_many_unsafe(key_iterator, flag=''):
    result = {}
    args = ['/sbin/postconf']
    if flag:
        args.append(flag)

    number_of_keys = 0
    for key in key_iterator:
        args.append(key)
        number_of_keys += 1

    stdout = _run(args)
    for line in filter(None, stdout.split('\n')):
        key, sep, value = line.partition('=')
        if not sep:
            raise ValueError('Invalid output detected')
        result[key.strip()] = value.strip()

    if len(result) != number_of_keys:
        raise ValueError('Some keys were missing from the output')
    return result


def set_many(kv_map):
    """Acquire resource lock. Set the list of postconf values as specified"""
    for key, value in kv_map.items():
        validate_key(key)
        validate_value(value)

    set_many_unsafe(kv_map)


def set_many_unsafe(kv_map, flag=''):
    args = ['/sbin/postconf']

    if not kv_map:
        return
    if flag:
        args.append(flag)
    for key, value in kv_map.items():
        args.append('{}={}'.format(key, value))
    _run(args)


def set_master_cf_options(service_flags, options={}):
    """Acquire resource lock. Set master.cf service options"""
    if not isinstance(service_flags, ServiceFlags):
        raise TypeError('service_flags')
    for key, value in options.items():
        validate_key(key)
        validate_value(value)

    service_key = service_flags.service + '/' + service_flags.type
    long_opts = {service_key + '/' + k: v for (k, v) in options.items()}

    logger.info('Setting %s service: %r', service_flags.service, options)

    # Crash resistant config setting:
    # /sbin/postconf -M "service/type=<temp flag string>"
    # /sbin/postconf -P "service/type/k=v" ...
    # Delete placeholder string /dev/null/plinth-crash
    set_unsafe(service_key, service_flags.serialize_temp(), '-M')
    set_many_unsafe(long_opts, '-P')
    _master_remove_crash_handler(service_flags)


def get_unsafe(key):
    """Get postconf value (no locking, no sanitization)"""
    result = _run(['/sbin/postconf', key])
    match = key + ' ='
    if not result.startswith(match):
        raise KeyError(key)
    return result[len(match):].strip()


def set_unsafe(key, value, flag=''):
    """Set postconf value (assuming root, no locking, no sanitization)"""
    if flag:
        _run(['/sbin/postconf', flag, '{}={}'.format(key, value)])
    else:
        _run(['/sbin/postconf', '{}={}'.format(key, value)])


def parse_maps(raw_value):
    if '{' in raw_value or '}' in raw_value:
        raise ValueError('Unsupported map list format')

    value_list = []
    for segment in raw_value.split(','):
        for sub_segment in segment.strip().split(' '):
            sub_segment = sub_segment.strip()
            if sub_segment:
                value_list.append(sub_segment)
    return value_list


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


def _master_remove_crash_handler(service_flags):
    with interproc.atomically_rewrite('/etc/postfix/master.cf') as writer:
        with open('/etc/postfix/master.cf') as reader:
            for line in reader:
                cleaned = service_flags.try_remove_crash_handler(line)
                writer.write(line if cleaned is None else cleaned)


def validate_key(key):
    """Validate postconf key format. Raises ValueError"""
    if not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', key):
        raise ValueError('Invalid postconf key format')


def validate_value(value):
    """Validate postconf value format. Raises ValueError"""
    for c in value:
        if ord(c) < 32:
            raise ValueError('Value contains control characters')
