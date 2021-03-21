# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for system diagnostics.
"""

import collections
import importlib
import logging
import pathlib
import threading

import psutil
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from plinth import app as app_module
from plinth import cfg, daemon, glib, menu
from plinth.modules.apache.components import diagnose_url_on_all
from plinth.modules.backups.components import BackupRestore

from . import manifest

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

        backup_restore = BackupRestore('backup-restore-diagnostics',
                                       **manifest.backup)
        self.add(backup_restore)

        # Check periodically for low RAM space
        interval = 180 if cfg.develop else 3600
        glib.schedule(interval, _warn_about_low_ram_space)

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

    running_task = threading.Thread(target=run_on_all_enabled_modules)
    running_task.start()


def run_on_all_enabled_modules():
    """Run diagnostics on all the enabled modules and store the result."""
    global current_results
    current_results = {
        'apps': [],
        'results': collections.OrderedDict(),
        'progress_percentage': 0
    }

    # Four result strings returned by tests, mark for translation and
    # translate later.
    ugettext_noop('passed')
    ugettext_noop('failed')
    ugettext_noop('error')
    ugettext_noop('warning')

    apps = []
    for app in app_module.App.list():
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
        app_name = app.info.name or app.app_id
        current_results['results'][app.app_id] = {'name': app_name}

    current_results['apps'] = apps
    for current_index, (app_id, app) in enumerate(apps):
        app_results = {
            'diagnosis': None,
            'exception': None,
        }

    global running_task
    running_task = None


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
        memory_available_unit = ugettext_noop('MiB')
        memory_available = memory_info['free_bytes'] / 1024**2
    else:
        # Translators: This is the unit of computer storage Gibibyte similar to
        # Gigabyte.
        memory_available_unit = ugettext_noop('GiB')
        memory_available = memory_info['free_bytes'] / 1024**3

    show = False
    if memory_info['percent_used'] > 90:
        severity = 'error'
        advice_message = ugettext_noop(
            'You should disable some apps to reduce memory usage.')
        show = True
    elif memory_info['percent_used'] > 75:
        severity = 'warning'
        advice_message = ugettext_noop(
            'You should not install any new apps on this system.')
        show = True

    if not show:
        try:
            Notification.get('diagnostics-low-ram-space').delete()
        except KeyError:
            pass
        return

    message = ugettext_noop(
        # xgettext:no-python-format
        'System is low on memory: {percent_used}% used, {memory_available} '
        '{memory_available_unit} free. {advice_message}')
    title = ugettext_noop('Low Memory')
    data = {
        'app_icon': 'fa-heartbeat',
        'app_name': 'translate:' + ugettext_noop('Diagnostics'),
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
