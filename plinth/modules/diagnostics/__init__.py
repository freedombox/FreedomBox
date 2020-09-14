# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for system diagnostics.
"""

import collections
import importlib
import logging
import threading

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from plinth import app as app_module
from plinth import daemon, menu
from plinth.modules.apache.components import diagnose_url_on_all

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

_description = [
    _('The system diagnostic test will run a number of checks on your '
      'system to confirm that applications and services are working as '
      'expected.')
]

app = None

logger = logging.Logger(__name__)

running_task = None

current_results = {}


class DiagnosticsApp(app_module.App):
    """FreedomBox app for diagnostics."""

    app_id = 'diagnostics'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential,
                               name=_('Diagnostics'), icon='fa-heartbeat',
                               description=_description,
                               manual_page='Diagnostics')
        self.add(info)

        menu_item = menu.Menu('menu-diagnostics', info.name, None, info.icon,
                              'diagnostics:index', parent_url_name='system')
        self.add(menu_item)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(daemon.diagnose_port_listening(8000, 'tcp4'))
        results.extend(
            diagnose_url_on_all('http://{host}/plinth/',
                                check_certificate=False))

        return results


def start_task():
    """Start the run task in a separate thread."""
    global running_task
    if running_task:
        raise Exception('Task already running')

    running_task = threading.Thread(target=_run_on_all_enabled_modules_wrapper)
    running_task.start()


def _run_on_all_enabled_modules_wrapper():
    """Wrapper over actual task to catch exceptions."""
    try:
        run_on_all_enabled_modules()
    except Exception as exception:
        logger.exception('Error running diagnostics - %s', exception)
        current_results['error'] = str(exception)

    global running_task
    running_task = None


def run_on_all_enabled_modules():
    """Run diagnostics on all the enabled modules and store the result."""
    global current_results
    current_results = {
        'apps': [],
        'results': collections.OrderedDict(),
        'progress_percentage': 0
    }

    # Three result strings returned by tests, mark for translation and
    # translate later.
    ugettext_noop('passed')
    ugettext_noop('failed')
    ugettext_noop('error')

    apps = []
    for app in app_module.App.list():
        # XXX: Implement more cleanly.
        # Don't run diagnostics on apps have not been setup yet.
        # However, run on apps that need an upgrade.
        module = importlib.import_module(app.__class__.__module__)
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        if not app.is_enabled():
            continue

        if not app.has_diagnostics():
            continue

        apps.append((app.app_id, app))
        current_results['results'][app.app_id] = None

    current_results['apps'] = apps
    for current_index, (app_id, app) in enumerate(apps):
        current_results['results'][app_id] = app.diagnose()
        current_results['progress_percentage'] = \
            int((current_index + 1) * 100 / len(apps))
