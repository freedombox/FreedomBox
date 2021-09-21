"""Configure email domains"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import json
import os
import re
import select
import subprocess
import sys
import time

from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from plinth.actions import superuser_run
from plinth.errors import ActionError
from plinth.modules.config import get_domainname

from . import models
from plinth.modules.email_server import interproc, postconf

EXIT_VALIDATION = 40

managed_keys = ['_mailname', 'mydomain', 'myhostname', 'mydestination']


class ClientError(RuntimeError):
    pass


def get():
    translation_table = [
        (check_postfix_domains, _('Postfix domain name config')),
    ]
    results = []
    with postconf.mutex.lock_all():
        for check, title in translation_table:
            results.append(check(title))
    return results


def repair():
    superuser_run('email_server', ['-i', 'domain', 'set_up'])


def repair_component(action_name):
    allowed_actions = {'set_up': ['postfix']}
    if action_name not in allowed_actions:
        return
    superuser_run('email_server', ['-i', 'domain', action_name])
    return allowed_actions[action_name]


def action_set_up():
    with postconf.mutex.lock_all():
        fix_postfix_domains(check_postfix_domains())


def check_postfix_domains(title=''):
    diagnosis = models.MainCfDiagnosis(title, action='set_up')
    domain = get_domainname() or 'localhost'
    postconf_keys = (k for k in managed_keys if not k.startswith('_'))
    conf = postconf.get_many_unsafe(postconf_keys, flag='-x')

    dest_set = set(postconf.parse_maps(conf['mydestination']))
    deletion_set = set()

    temp = _amend_mailname(domain)
    if temp is not None:
        diagnosis.error('Set /etc/mailname to %s', temp)
        diagnosis.flag('_mailname', temp)

    # Amend $mydomain and conf['mydomain']
    temp = _amend_mydomain(conf['mydomain'], domain)
    if temp is not None:
        diagnosis.error('Set $mydomain to %s', temp)
        diagnosis.flag('mydomain', temp)
        deletion_set.add(conf['mydomain'])
        conf['mydomain'] = temp

    # Amend $myhostname and conf['myhostname']
    temp = _amend_myhostname(conf['myhostname'], conf['mydomain'])
    if temp is not None:
        diagnosis.error('Set $myhostname to %s', temp)
        diagnosis.flag('myhostname', temp)
        deletion_set.add(conf['myhostname'])
        conf['myhostname'] = temp

    # Delete old domain names
    deletion_set.discard('localhost')
    dest_set.difference_update(deletion_set)

    # Amend $mydestination
    temp = _amend_mydestination(dest_set, conf['mydomain'], conf['myhostname'],
                                diagnosis.error)
    if temp is not None:
        diagnosis.flag('mydestination', temp)
    elif len(deletion_set) > 0:
        corrected_value = ', '.join(sorted(dest_set))
        diagnosis.error('Update $mydestination')
        diagnosis.flag('mydestination', corrected_value)

    return diagnosis


def _amend_mailname(domain):
    with open('/etc/mailname', 'r') as fd:
        mailname = fd.readline().strip()

    # If mailname is not localhost, refresh it
    if mailname != 'localhost':
        temp = _change_to_domain_name(mailname, domain, False)
        if temp != mailname:
            return temp

    return None


def _amend_mydomain(conf_value, domain):
    temp = _change_to_domain_name(conf_value, domain, False)
    if temp != conf_value:
        return temp

    return None


def _amend_myhostname(conf_value, mydomain):
    if conf_value != mydomain:
        if not conf_value.endswith('.' + mydomain):
            return mydomain

    return None


def _amend_mydestination(dest_set, mydomain, myhostname, error):
    addition_set = set()
    if mydomain not in dest_set:
        error('Value of $mydomain is not in $mydestination')
        addition_set.add('$mydomain')
        addition_set.add('$myhostname')
    if myhostname not in dest_set:
        error('Value of $myhostname is not in $mydestination')
        addition_set.add('$mydomain')
        addition_set.add('$myhostname')
    if 'localhost' not in dest_set:
        error('localhost is not in $mydestination')
        addition_set.add('localhost')

    if addition_set:
        addition_set.update(dest_set)
        return ', '.join(sorted(addition_set))

    return None


def _change_to_domain_name(value, domain, allow_old_fqdn):
    # Detect invalid values
    if not value or '.' not in value:
        return domain

    if not allow_old_fqdn and value != domain:
        return domain
    else:
        return value


def fix_postfix_domains(diagnosis):
    diagnosis.apply_changes(_apply_domain_changes)


def _apply_domain_changes(conf_dict):
    for key, value in conf_dict.items():
        if key.startswith('_'):
            update = globals()['su_set' + key]
            update(value)

    post = {k: v for (k, v) in conf_dict.items() if not k.startswith('_')}
    postconf.set_many_unsafe(post)


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

    # Important: reload postfix after acquiring lock
    with postconf.mutex.lock_all():
        # systemctl reload postfix
        args = ['systemctl', 'reload', 'postfix']
        completed = subprocess.run(args, capture_output=True)
        if completed.returncode != 0:
            interproc.log_subprocess(completed)
            raise OSError('Could not reload postfix')


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
    with interproc.atomically_rewrite('/etc/mailname') as fd:
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
