# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Set and get postfix configuration using postconf.

See: http://www.postfix.org/postconf.1.html
See: http://www.postfix.org/master.5.html
See: http://www.postfix.org/postconf.5.html
"""

import re
import subprocess
from dataclasses import dataclass

from plinth import action_utils


@dataclass
class Service:  # NOQA, pylint: disable=too-many-instance-attributes
    """Representation of a postfix daemon and its options."""
    service: str
    type_: str
    private: str
    unpriv: str
    chroot: str
    wakeup: str
    maxproc: str
    command: str
    options: dict[str, str]

    def __str__(self) -> str:
        parts = [
            self.service, self.type_, self.private, self.unpriv, self.chroot,
            self.wakeup, self.maxproc, self.command
        ]
        for key, value in self.options.items():
            _validate_key(key)
            _validate_value(value)
            parts.extend(['-o', f'{key}={value}'])

        return ' '.join(parts)


def get_config(keys: list) -> dict:
    """Get postfix configuration using the postconf command."""
    for key in keys:
        _validate_key(key)

    args = ['/sbin/postconf']
    for key in keys:
        args.append(key)

    output = _run(args)
    result = {}
    lines: list[str] = list(filter(None, output.split('\n')))
    for line in lines:
        key, sep, value = line.partition('=')
        if not sep:
            raise ValueError('Invalid output detected')

        result[key.strip()] = value.strip()

    if set(keys) != set(result.keys()):
        raise ValueError('Some keys were missing from the output')

    return result


def set_config(config: dict, flag=None):
    """Set postfix configuration using the postconf command."""
    if not config:
        return

    for key, value in config.items():
        _validate_key(key)
        _validate_value(value)

    args = ['/sbin/postconf']
    if flag:
        args.append(flag)

    for key, value in config.items():
        args.append('{}={}'.format(key, value))

    _run(args)


def set_master_config(service: Service):
    """Set daemons and their options in postfix master.cf."""
    service_key = service.service + '/' + service.type_
    set_config({service_key: str(service)}, '-M')


def parse_maps(raw_value):
    """Parse postfix configuration values that are maps."""
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
    """Run process. Capture and return standard output as a string.

    Raise a RuntimeError on non-zero exit codes.
    """
    try:
        result = action_utils.run(args, check=True, capture_output=True)
        return result.stdout.decode()
    except subprocess.SubprocessError as subprocess_error:
        raise RuntimeError('Subprocess failed') from subprocess_error
    except UnicodeDecodeError as unicode_error:
        raise RuntimeError('Unicode decoding failed') from unicode_error


def _validate_key(key):
    """Validate postconf key format or raise ValueError."""
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_/]*$', key):
        raise ValueError('Invalid postconf key format')


def _validate_value(value):
    """Validate postconf value format or raise ValueError."""
    for char in value:
        if ord(char) < 32:
            raise ValueError('Value contains control characters')
