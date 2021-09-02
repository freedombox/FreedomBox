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
    translation = {
        'rc_installed': _('RoundCube availability'),
        'rc_config_header': _('RoundCube configured for FreedomBox email'),
    }

    output = actions.superuser_run('email_server', ['-i', 'rcube', 'check'])
    results = json.loads(output)
    for i in range(0, len(results)):
        results[i] = models.Diagnosis.from_json(results[i], translation.get)

    return results


def repair():
    actions.superuser_run('email_server', ['-i', 'rcube', 'set_up'])


def repair_component(action):
    action_to_services = {'set_up': []}
    if action not in action_to_services:
        return
    actions.superuser_run('email_server', ['-i', 'rcube', action])
    return action_to_services[action]


def action_check():
    results = _action_check()
    for i in range(0, len(results)):
        results[i] = results[i].to_json()
    print(json.dumps(results))


def _action_check():
    results = []
    if not os.path.exists(config_path):
        diagnosis = models.Diagnosis('rc_installed')
        diagnosis.error('Config file was missing')
        diagnosis.error('Check that RoundCube has been installed')
        results.append(diagnosis)
        return results

    diagnosis = models.Diagnosis('rc_config_header', action='set_up')
    injector = ConfigInjector(boundary_pattern, boundary_format)
    if not injector.has_header_line(config_path):
        diagnosis.error('FreedomBox header line was missing')
    results.append(diagnosis)
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
