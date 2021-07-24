"""Configure email domains"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib
import io
import json
import os
import re
import select
import sys
import time
import uuid

from types import SimpleNamespace

from django.core.exceptions import ValidationError
from plinth.errors import ActionError
from plinth.actions import superuser_run

from . import models
from plinth.modules.email_server import postconf

EXIT_VALIDATION = 40

managed_keys = ['_mailname', 'mydomain', 'myhostname', 'mydestination']


class ClientError(RuntimeError):
    pass


def get():
    # Stub
    return [models.Diagnosis('Email domains')]


def repair():
    # Stub
    raise RuntimeError()


def get_domain_config():
    fields = []

    # Special keys
    mailname = SimpleNamespace(key='_mailname', name='/etc/mailname')
    with open('/etc/mailname', 'r') as fd:
        mailname.value = fd.readline().strip()
    fields.append(mailname)

    # Postconf keys
    postconf_keys = [k for k in managed_keys if not k.startswith('_')]
    result_dict = postconf.get_many(postconf_keys)
    for key, value in result_dict.items():
        field = SimpleNamespace(key=key, value=value, name='$' + key)
        fields.append(field)

    return fields


def set_keys(raw):
    # Serialize the keys we know
    config_dict = {k: v for (k, v) in raw.items() if k in managed_keys}
    if not config_dict:
        raise ClientError('To update a key, specify a new value')

    ipc = b'%s\n' % json.dumps(config_dict).encode('utf8')
    if len(ipc) > 4096:
        raise ClientError('POST data exceeds max line length')

    try:
        superuser_run('email_server', ['-i', 'domain', 'set_keys'], input=ipc)
    except ActionError as e:
        stdout = e.args[1]
        if not stdout.startswith('ClientError:'):
            raise RuntimeError('Action script failure') from e
        else:
            raise ValidationError(stdout) from e


def action_set_keys():
    try:
        _action_set_keys()
    except ClientError as e:
        print('ClientError:', end=' ')
        print(e.args[0])
        sys.exit(EXIT_VALIDATION)


def _action_set_keys():
    line = _stdin_readline()
    if not line.startswith('{') or not line.endswith('}\n'):
        raise ClientError('Bad stdin data')

    clean_dict = {}
    # Input validation
    for key, value in json.loads(line).items():
        if key not in managed_keys:
            raise ClientError('Key not allowed: %r' % key)
        if not isinstance(value, str):
            raise ClientError('Bad value type from key: %r' % key)
        clean_function = globals()['clean_' + key.lstrip('_')]
        clean_dict[key] = clean_function(value)

    # Apply changes (postconf)
    postconf_dict = dict(filter(lambda kv: not kv[0].startswith('_'),
                                clean_dict.items()))
    postconf.set_many(postconf_dict)

    # Apply changes (special)
    for key, value in clean_dict.items():
        if key.startswith('_'):
            set_function = globals()['su_set' + key]
            set_function(value)


def clean_mailname(mailname):
    mailname = mailname.lower().strip()
    if not re.match('^[a-z0-9-\\.]+$', mailname):
        raise ClientError('Invalid character in host/domain/mail name')
    # XXX: need more verification
    return mailname


def clean_mydomain(raw):
    return clean_mailname(raw)


def clean_myhostname(raw):
    return clean_mailname(raw)


def clean_mydestination(raw):
    ascii_code = (ord(c) for c in raw)
    valid = all(32 <= a <= 126 for a in ascii_code)
    if not valid:
        raise ClientError('Bad input for $mydestination')
    else:
        return raw


def su_set_mailname(cleaned):
    with _atomically_rewrite('/etc/mailname', 'x') as fd:
        fd.write(cleaned)
        fd.write('\n')


def _stdin_readline():
    membuf = io.BytesIO()
    bytes_saved = 0
    fd = sys.stdin.buffer
    time_started = time.monotonic()

    # Reading stdin with timeout
    # https://stackoverflow.com/a/21429655
    os.set_blocking(fd.fileno(), False)

    while bytes_saved < 4096:
        rlist, wlist, xlist = select.select([fd], [], [], 1.0)
        if fd in rlist:
            data = os.read(fd.fileno(), 4096)
            membuf.write(data)
            bytes_saved += len(data)
            if len(data) == 0 or b'\n' in data:  # end of file or line
                break
        if time.monotonic() - time_started > 5:
            raise TimeoutError()

    # Read a line
    membuf.seek(0)
    line = membuf.readline()
    if not line.endswith(b'\n'):
        raise ClientError('Line was too long')

    try:
        return line.decode('utf8')
    except ValueError as e:
        raise ClientError('UTF-8 decode failed') from e


@contextlib.contextmanager
def _atomically_rewrite(filepath, mode):
    successful = False
    tmp = '%s.%s.plinth-tmp' % (filepath, uuid.uuid4().hex)
    fd = open(tmp, mode)

    try:
        # Let client write to a temporary file
        yield fd
        successful = True
    finally:
        fd.close()

    try:
        if successful:
            # Invoke rename(2) to atomically replace the original
            os.rename(tmp, filepath)
    finally:
        # Delete temp file
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
