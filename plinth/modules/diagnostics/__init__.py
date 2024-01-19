# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for system diagnostics.
"""

import collections
import json
import logging
import pathlib
import threading
from copy import deepcopy

import psutil
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import daemon, glib, kvstore, menu
from plinth import operation as operation_module
from plinth.modules.apache.components import diagnose_url_on_all
from plinth.modules.backups.components import BackupRestore

from . import manifest
from .check import CheckJSONDecoder, CheckJSONEncoder, Result

_description = [
    _('The system diagnostic test will run a number of checks on your '
      'system to confirm that applications and services are working as '
      'expected.')
]

logger = logging.Logger(__name__)

current_results = {}
results_lock = threading.Lock()


class DiagnosticsApp(app_module.App):
    """FreedomBox app for diagnostics."""

    app_id = 'diagnostics'

    _version = 1

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Diagnostics'),
                               icon='fa-heartbeat', description=_description,
                               manual_page='Diagnostics')
        self.add(info)

        menu_item = menu.Menu('menu-diagnostics', info.name, None, info.icon,
                              'diagnostics:index', parent_url_name='system')
        self.add(menu_item)

        backup_restore = BackupRestore('backup-restore-diagnostics',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        # Check periodically for low RAM space
        glib.schedule(3600, _warn_about_low_ram_space)

        # Run diagnostics once a day
        glib.schedule(24 * 3600, start_diagnostics, in_thread=False)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(daemon.diagnose_port_listening(8000, 'tcp4'))
        results.extend(
            diagnose_url_on_all('http://{host}/plinth/',
                                check_certificate=False))

        return results


def _run_on_all_enabled_modules():
    """Run diagnostics on all the enabled modules and store the result."""
    global current_results

    # Four result strings returned by tests, mark for translation and
    # translate later.
    gettext_noop('passed')
    gettext_noop('failed')
    gettext_noop('error')
    gettext_noop('warning')

    apps = []

    with results_lock:
        current_results = {
            'apps': [],
            'results': collections.OrderedDict(),
            'progress_percentage': 0
        }

        for app in app_module.App.list():
            # Don't run diagnostics on apps have not been setup yet.
            # However, run on apps that need an upgrade.
            if app.needs_setup():
                continue

            if not app.is_enabled():
                continue

            if not app.has_diagnostics():
                continue

            apps.append((app.app_id, app))
            current_results['results'][app.app_id] = {'id': app.app_id}

        current_results['apps'] = apps

    for current_index, (app_id, app) in enumerate(apps):
        app_results = {
            'diagnosis': None,
            'exception': None,
            'show_rerun_setup': False,
        }

        try:
            app_results['diagnosis'] = app.diagnose()
        except Exception as exception:
            logger.exception('Error running %s diagnostics - %s', app_id,
                             exception)
            app_results['exception'] = str(exception)

        for check in app_results['diagnosis']:
            if check.result in [Result.FAILED, Result.WARNING]:
                app_results['show_rerun_setup'] = True
                break

        with results_lock:
            current_results['results'][app_id].update(app_results)
            current_results['progress_percentage'] = \
                int((current_index + 1) * 100 / len(apps))


def _get_memory_info_from_cgroups():
    """Return information about RAM usage from cgroups."""
    cgroups_memory_path = pathlib.Path('/sys/fs/cgroup/memory')
    memory_limit_file = cgroups_memory_path / 'memory.limit_in_bytes'
    memory_usage_file = cgroups_memory_path / 'memory.usage_in_bytes'
    memory_stat_file = cgroups_memory_path / 'memory.stat'

    try:
        memory_total = int(memory_limit_file.read_text())
        memory_usage = int(memory_usage_file.read_text())
        memory_stat_lines = memory_stat_file.read_text().split('\n')
    except OSError:
        return {}

    memory_inactive = int([
        line.rsplit(maxsplit=1)[1] for line in memory_stat_lines
        if line.startswith('total_inactive_file')
    ][0])
    memory_used = memory_usage - memory_inactive

    return {
        'total_bytes': memory_total,
        'percent_used': memory_used * 100 / memory_total,
        'free_bytes': memory_total - memory_used
    }


def _get_memory_info():
    """Return RAM usage information."""
    memory_info = psutil.virtual_memory()

    cgroups_memory_info = _get_memory_info_from_cgroups()
    if cgroups_memory_info and cgroups_memory_info[
            'total_bytes'] < memory_info.total:
        return cgroups_memory_info

    return {
        'total_bytes': memory_info.total,
        'percent_used': memory_info.percent,
        'free_bytes': memory_info.available
    }


def _warn_about_low_ram_space(request):
    """Warn about insufficient RAM space."""
    from plinth.notification import Notification

    memory_info = _get_memory_info()
    if memory_info['free_bytes'] < 1024**3:
        # Translators: This is the unit of computer storage Mebibyte similar to
        # Megabyte.
        memory_available_unit = gettext_noop('MiB')
        memory_available = memory_info['free_bytes'] / 1024**2
    else:
        # Translators: This is the unit of computer storage Gibibyte similar to
        # Gigabyte.
        memory_available_unit = gettext_noop('GiB')
        memory_available = memory_info['free_bytes'] / 1024**3

    show = False
    if memory_info['percent_used'] > 90:
        severity = 'error'
        advice_message = gettext_noop(
            'You should disable some apps to reduce memory usage.')
        show = True
    elif memory_info['percent_used'] > 75:
        severity = 'warning'
        advice_message = gettext_noop(
            'You should not install any new apps on this system.')
        show = True

    if not show:
        try:
            Notification.get('diagnostics-low-ram-space').delete()
        except KeyError:
            pass
        return

    message = gettext_noop(
        # xgettext:no-python-format
        'System is low on memory: {percent_used}% used, {memory_available} '
        '{memory_available_unit} free. {advice_message}')
    title = gettext_noop('Low Memory')
    data = {
        'app_icon': 'fa-heartbeat',
        'app_name': 'translate:' + gettext_noop('Diagnostics'),
        'percent_used': f'{memory_info["percent_used"]:.1f}',
        'memory_available': f'{memory_available:.1f}',
        'memory_available_unit': 'translate:' + memory_available_unit,
        'advice_message': 'translate:' + advice_message
    }
    actions = [{'type': 'dismiss'}]
    Notification.update_or_create(id='diagnostics-low-ram-space',
                                  app_id='diagnostics', severity=severity,
                                  title=title, message=message,
                                  actions=actions, data=data, group='admin')


def start_diagnostics(data: None = None):
    """Start full diagnostics as a background operation."""
    logger.info('Running full diagnostics')
    try:
        operation_module.manager.new(op_id='diagnostics-full',
                                     app_id='diagnostics',
                                     name=gettext_noop('Running diagnostics'),
                                     target=_run_diagnostics,
                                     show_message=False,
                                     show_notification=False)
    except KeyError:
        logger.warning('Diagnostics are already running')


def _run_diagnostics():
    """Run diagnostics and notify for failures."""
    from plinth.notification import Notification

    _run_on_all_enabled_modules()
    with results_lock:
        results = current_results['results']
        # Store the most recent results in the database.
        kvstore.set('diagnostics_results',
                    json.dumps(results, cls=CheckJSONEncoder))

        issue_count = 0
        severity = 'warning'
        for _app_id, app_data in results.items():
            if app_data['exception']:
                issue_count += 1
                severity = 'error'
            else:
                for check in app_data['diagnosis']:
                    if check.result != Result.PASSED:
                        issue_count += 1
                        if check.result != Result.WARNING:
                            severity = 'error'

    if not issue_count:
        # Remove any previous notifications if there are no issues.
        try:
            Notification.get('diagnostics-background').delete()
        except KeyError:
            pass

        return

    message = gettext_noop(
        # xgettext:no-python-format
        'Found {issue_count} issues during routine tests.')
    title = gettext_noop('Diagnostics results')
    data = {'app_icon': 'fa-heartbeat', 'issue_count': issue_count}
    actions = [{
        'type': 'link',
        'class': 'primary',
        'text': gettext_noop('Go to diagnostics results'),
        'url': 'diagnostics:full'
    }, {
        'type': 'dismiss'
    }]
    note = Notification.update_or_create(id='diagnostics-background',
                                         app_id='diagnostics',
                                         severity=severity, title=title,
                                         message=message, actions=actions,
                                         data=data, group='admin')
    note.dismiss(False)


def are_results_available():
    """Return whether diagnostic results are available."""
    with results_lock:
        results = current_results

    if not results:
        results = kvstore.get_default('diagnostics_results', '{}')
        results = json.loads(results)

    return bool(results)


def get_results():
    """Return the latest results of full diagnostics."""
    with results_lock:
        results = deepcopy(current_results)

    # If no results are available in memory, then load from database.
    if not results:
        results = kvstore.get_default('diagnostics_results', '{}')
        results = json.loads(results, cls=CheckJSONDecoder)
        results = {'results': results, 'progress_percentage': 100}

    # Add a translated name for each app
    for app_id in results['results']:
        app = app_module.App.get(app_id)
        results['results'][app_id]['name'] = app.info.name or app_id

    return results
