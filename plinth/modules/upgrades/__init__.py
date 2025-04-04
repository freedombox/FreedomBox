# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for upgrades."""

import datetime
import logging
import os
import subprocess

from aptsources import sourceslist
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

import plinth
from plinth import action_utils
from plinth import app as app_module
from plinth import cfg, glib, kvstore, menu, package
from plinth.config import DropinConfigs
from plinth.daemon import RelatedDaemon
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import distupgrade, manifest, privileged

first_boot_steps = [
    {
        'id': 'backports_wizard',
        'url': 'upgrades:backports-firstboot',
        'order': 5,
    },
]

_description = [
    _('Check for and apply the latest software and security updates.'),
    _('Updates are run at 06:00 everyday according to local time zone. Set '
      'your time zone in Date & Time app. Apps are restarted after update '
      'causing them to be unavailable briefly. If system reboot is deemed '
      'necessary, it is done automatically at 02:00 causing all apps to be '
      'unavailable briefly.')
]

BACKPORTS_REQUESTED_KEY = 'upgrades_backports_requested'

DIST_UPGRADE_ENABLED_KEY = 'upgrades_dist_upgrade_enabled'

DIST_UPGRADE_RUN_HOUR = 6  # 06:00 (morning)

PKG_HOLD_DIAG_CHECK_ID = 'upgrades-package-holds'

logger = logging.getLogger(__name__)


class UpgradesApp(app_module.App):
    """FreedomBox app for software upgrades."""

    app_id = 'upgrades'

    _version = 18

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Software Update'),
                               icon='fa-refresh', description=_description,
                               manual_page='Upgrades', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-upgrades', info.name, info.icon, info.tags,
                              'upgrades:index',
                              parent_url_name='system:system', order=50)
        self.add(menu_item)

        packages = Packages('packages-upgrades',
                            ['unattended-upgrades', 'needrestart'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-upgrades', [
            '/etc/apt/apt.conf.d/20freedombox',
            '/etc/apt/apt.conf.d/20freedombox-allow-release-info-change',
            '/etc/apt/apt.conf.d/60unattended-upgrades',
            '/etc/needrestart/conf.d/freedombox.conf',
        ])
        self.add(dropin_configs)

        daemon = RelatedDaemon('related-daemon-upgrades',
                               'freedombox-dist-upgrade')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-upgrades',
                                       **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        self._show_new_release_notification()

        # Check every day if backports becomes available, then configure it if
        # selected by user.
        glib.schedule(24 * 3600, setup_repositories)

        # Check every day if new stable release becomes available and if we
        # waited enough, then perform dist-upgrade if updates are enabled.
        glib.schedule(3600, check_dist_upgrade)

    def _show_new_release_notification(self):
        """When upgraded to new release, show a notification."""
        from plinth.notification import Notification
        try:
            note = Notification.get('upgrades-new-release')
            if note.data['version'] == plinth.__version__:
                # User already has notification for update to this version. It
                # may be dismissed or not yet dismissed
                return

            # User currently has a notification for an older version, update.
            dismiss = False
        except KeyError:
            # Don't show notification for the first version user runs, create
            # but don't show it.
            dismiss = True

        data = {
            'version': plinth.__version__,
            'app_name': 'translate:' + gettext_noop('Software Update'),
            'app_icon': 'fa-refresh'
        }
        title = gettext_noop('FreedomBox Updated')
        note = Notification.update_or_create(
            id='upgrades-new-release', app_id='upgrades', severity='info',
            title=title, body_template='upgrades-new-release.html', data=data,
            group='admin')
        note.dismiss(should_dismiss=dismiss)

    def _show_first_manual_update_notification(self):
        """After first setup, show notification to manually run updates."""
        from plinth.notification import Notification
        title = gettext_noop('Run software update manually')
        message = gettext_noop(
            'Automatic software update runs daily by default. For the first '
            'time, manually run it now.')
        data = {
            'app_name': 'translate:' + gettext_noop('Software Update'),
            'app_icon': 'fa-refresh'
        }
        actions = [{
            'type': 'link',
            'class': 'primary',
            'text': gettext_noop('Go to {app_name}'),
            'url': 'upgrades:index'
        }, {
            'type': 'dismiss'
        }]
        Notification.update_or_create(id='upgrades-first-manual-update',
                                      app_id='upgrades', severity='info',
                                      title=title, message=message,
                                      actions=actions, data=data,
                                      group='admin', dismissed=False)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        # Enable automatic upgrades but only on first install
        if not old_version and not cfg.develop:
            privileged.enable_auto()

        # Request user to run manual update as a one time activity
        if not old_version:
            self._show_first_manual_update_notification()

        # Update apt preferences whenever on first install and on version
        # increment.
        privileged.setup()

        # When upgrading from a version without first boot wizard for
        # backports, assume backports have been requested.
        if old_version and old_version < 7:
            set_backports_requested(can_activate_backports())

        # Enable dist upgrade for new installs, and once when upgrading
        # from version without flag.
        if not old_version or old_version < 8:
            set_dist_upgrade_enabled(can_enable_dist_upgrade())

        # Try to setup apt repositories, if needed, if possible, on first
        # install and on version increment.
        setup_repositories(None)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(_diagnose_held_packages())
        return results

    def repair(self, failed_checks: list) -> bool:
        """Handle repair for custom diagnostic."""
        remaining_checks = []
        for check in failed_checks:
            if check.check_id == PKG_HOLD_DIAG_CHECK_ID:
                privileged.release_held_packages()
            else:
                remaining_checks.append(check)

        return super().repair(remaining_checks)


def setup_repositories(_):
    """Setup apt repositories for backports."""
    if is_backports_requested():
        privileged.activate_backports(cfg.develop)


def check_dist_upgrade(_):
    """Check for upgrade to new stable release."""
    # Run once a day at a desired hour even when triggered every hour. There is
    # a small chance that this won't run in a given day.
    now = datetime.datetime.now()  # Local timezone
    if now.hour != DIST_UPGRADE_RUN_HOUR:
        return

    if is_dist_upgrade_enabled():
        status = distupgrade.get_status()
        starting = status['next_action'] in ('continue', 'ready')
        dist_upgrade_show_notification(status, starting)
        if starting:
            logger.info('Starting distribution upgrade - %s', status)
            privileged.start_dist_upgrade()
        else:
            logger.info('Not ready for distribution upgrade - %s', status)


def dist_upgrade_show_notification(status: dict, starting: bool):
    """Show various notifications regarding distribution upgrade.

    - Show a notification 60 days, 30 days, 1 week, and 1 day before
      distribution upgrade. If a notification is dismissed for any of these
      periods don't show again until new period starts. Override any previous
      notification.

    - Show a notification just before the distribution upgrade showing that the
      process has started. Override any previous notification.

    - Show a notification after the distribution upgrade is completed that it
      is done. Override any previous notification. Keep this until it is 60
      days before next distribution upgrade. If user dismisses the
      notification, don't show it again.
    """
    from plinth.notification import Notification

    try:
        note = Notification.get('upgrades-dist-upgrade')
        data = note.data
    except KeyError:
        data = {}

    in_days = None
    if status['next_action_date']:
        in_days = (status['next_action_date'] -
                   datetime.datetime.now(tz=datetime.timezone.utc))

    if in_days is None or in_days > datetime.timedelta(days=60):
        for_days = None
    elif in_days > datetime.timedelta(days=30):
        for_days = 60  # 60 day notification
    elif in_days > datetime.timedelta(days=7):
        for_days = 30  # 30 day notification
    elif in_days > datetime.timedelta(days=1):
        for_days = 7  # 1 week notification
    else:
        for_days = 1  # 1 day notification, or overdue notification

    if status['running']:
        # Do nothing while the distribution upgrade is running.
        return

    state = 'starting' if starting else 'waiting'
    if (not for_days and status['current_codename']
            and data.get('next_codename') == status['current_codename']):
        # Previously shown notification's codename is current codename.
        # Distribution upgrade was successfully completed.
        state = 'done'

    if not status['next_action'] and state != 'done':
        # There is no upgrade available, don't show any notification.
        return

    if not for_days and data.get('state') == 'done':
        # Don't remove notification showing upgrade is complete until next
        # distribution upgrade is coming up in 2 months or sooner.
        return

    if not for_days and state == 'waiting':
        # More than 60 days to next distribution update. Don't show
        # notification.
        return

    if (for_days == data.get('for_days') and state == data.get('state')
            and status['next_codename'] == data.get('next_codename')):
        # If the notification was shown for same distribution codename, same
        # duration, and same state, then don't show it again.
        return

    data = {
        'app_name': 'translate:' + gettext_noop('Software Update'),
        'app_icon': 'fa-refresh',
        'current_codename': status['current_codename'],
        'current_version': status['current_version'],
        'next_codename': status['next_codename'],
        'next_version': status['next_version'],
        'state': state,
        'for_days': for_days,
        'in_days': in_days.days if in_days else None,
    }
    title = gettext_noop('Distribution Update')
    note = Notification.update_or_create(
        id='upgrades-dist-upgrade', app_id='upgrades', severity='info',
        title=title, body_template='upgrades-dist-upgrade-notification.html',
        data=data, group='admin')
    note.dismiss(should_dismiss=False)


def is_backports_requested():
    """Return whether user has chosen to activate backports."""
    return kvstore.get_default(BACKPORTS_REQUESTED_KEY, False)


def set_backports_requested(requested):
    """Set whether user has chosen to activate backports."""
    kvstore.set(BACKPORTS_REQUESTED_KEY, requested)
    logger.info('Backports requested - %s', requested)


def is_dist_upgrade_enabled():
    """Return whether user has enabled dist upgrade."""
    return kvstore.get_default(DIST_UPGRADE_ENABLED_KEY, False)


def set_dist_upgrade_enabled(enabled=True):
    """Set whether user has enabled dist upgrade."""
    kvstore.set(DIST_UPGRADE_ENABLED_KEY, enabled)
    logger.info('Distribution upgrade configured - %s', enabled)


def is_backports_enabled():
    """Return whether backports are enabled in the system configuration."""
    return os.path.exists(privileged.BACKPORTS_SOURCES_LIST)


def get_current_release():
    """Return current release and codename as a tuple."""
    output = subprocess.check_output(
        ['lsb_release', '--release', '--codename',
         '--short']).decode().strip()
    lines = output.split('\n')
    return lines[0], lines[1]


def is_backports_current():
    """Return whether backports are enabled for the current release."""
    if not is_backports_enabled():
        return False

    _, dist = get_current_release()
    dist += '-backports'
    sources = sourceslist.SourcesList()
    for source in sources:
        if source.dist == dist:
            return True

    return False


def can_activate_backports():
    """Return whether backports can be activated."""
    if cfg.develop:
        return True

    # Release will be 'n/a' in latest unstable and testing distributions.
    release, _ = get_current_release()
    return release not in ['unstable', 'testing', 'n/a']


def can_enable_dist_upgrade():
    """Return whether dist upgrade can be enabled."""
    release, _ = get_current_release()
    return release not in ['unstable', 'testing', 'n/a']


def _diagnose_held_packages():
    """Check if any packages have holds."""
    check = DiagnosticCheck(PKG_HOLD_DIAG_CHECK_ID,
                            gettext_noop('Check for package holds'),
                            Result.NOT_DONE)
    if (package.is_package_manager_busy()
            or action_utils.service_is_running('freedombox-dist-upgrade')):
        check.result = Result.SKIPPED
        return check

    output = subprocess.check_output(['apt-mark', 'showhold']).decode().strip()
    held_packages = output.split()
    check.result = Result.FAILED if held_packages else Result.PASSED
    return check
