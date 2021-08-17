# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import logging
import os

from django.utils.translation import ugettext_lazy as _
from plinth import actions

from . import models
from plinth.modules.email_server.lock import Mutex
from plinth.modules.email_server.modconf import ConfigInjector


config_path = '/etc/roundcube/config.inc.php'
boundary_pattern = '//[ ]*--[ ]*(BEGIN|END)[ ]+FREEDOMBOX CONFIG$'
boundary_format = '//-- {} FREEDOMBOX CONFIG'

rconf_template = """//
// The following section is managed by FreedomBox
// Be careful not to edit
include_once("/etc/roundcube/freedombox_mail.inc.php");
"""

logger = logging.getLogger(__name__)
rcube_mutex = Mutex('rcube-config')


def get():
    translation_table = {
        'rc_installed': _('RoundCube availability'),
        'rc_config_header': _('FreedomBox header in RoundCube config'),
    }
    output = actions.superuser_run('email_server', ['-i', 'rcube', 'check'])
    results = json.loads(output)
    for i in range(0, len(results)):
        name = translation_table.get(results[i][0], results[i][0])
        diagnosis = models.Diagnosis(name)
        if results[i][1] == 'error':
            diagnosis.error('Failed')
        results[i] = diagnosis

    return results


def repair():
    actions.superuser_run('email_server', ['-i', 'rcube', 'set_up'])


def action_check():
    results = _action_check()
    print(json.dumps(results))


def _action_check():
    results = []
    if not os.path.exists(config_path):
        results.append(['rc_installed', 'error'])
        return results

    injector = ConfigInjector(boundary_pattern, boundary_format)
    if injector.has_header_line(config_path):
        results.append(['rc_config_header', 'pass'])
    else:
        results.append(['rc_config_header', 'error'])

    return results


def action_set_up():
    with rcube_mutex.lock_all():
        _inject_rcube_config()


def _inject_rcube_config():
    if not os.path.exists(config_path):
        logger.warning('Roundcube has not been installed')
        return
    logger.info('Opening rcube config file %s', config_path)
    injector = ConfigInjector(boundary_pattern, boundary_format)
    injector.do_template_string(rconf_template, config_path)
