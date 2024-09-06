# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for upgrades."""

import logging
import os
import subprocess

from aptsources import sourceslist
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

import plinth
from plinth import app as app_module
from plinth import action_utils, cfg, glib, kvstore, menu, package
from plinth.config import DropinConfigs
from plinth.daemon import RelatedDaemon
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import manifest, privileged

first_boot_steps = [
    {
        'id': 'backports_wizard',
        'url': 'upgrades:backports-firstboot',
        'order': 5,
    },
    {
        'id': 'initial_update',
        'url': 'upgrades:update-firstboot',
        'order': 6,
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
                               manual_page='Upgrades')
        self.add(info)

        menu_item = menu.Menu('menu-upgrades', info.name, None, info.icon,
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

        # Check every day if new stable release becomes available, then perform
        # dist-upgrade if updates are enabled
        glib.schedule(24 * 3600, check_dist_upgrade)

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

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        # Enable automatic upgrades but only on first install
        if not old_version and not cfg.develop:
            privileged.enable_auto()

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
    if is_dist_upgrade_enabled():
        try_start_dist_upgrade()


def try_start_dist_upgrade(test=False):
    """Try to start dist upgrade."""
    from plinth.notification import Notification

    result = privileged.start_dist_upgrade(test)
    dist_upgrade_started = result['dist_upgrade_started']
    reason = result['reason']
    if 'found-previous' in reason:
        logger.info(
            'Found previous dist-upgrade. If it was interrupted, it will '
            'be restarted.')
    elif 'already-' in reason:
        logger.info('Skip dist upgrade: System is already up-to-date.')
    elif 'codename-not-found' in reason:
        logger.warning('Skip dist upgrade: Codename not found in release '
                       'file.')
    elif 'upgrades-not-enabled' in reason:
        logger.info('Skip dist upgrade: Automatic updates are not enabled.')
    elif 'test-not-set' in reason:
        logger.info('Skip dist upgrade: --test is not set.')
    elif 'not-enough-free-space' in reason:
        logger.warning('Skip dist upgrade: Not enough free space in /.')
        title = gettext_noop('Could not start distribution update')
        message = gettext_noop(
            'There is not enough free space in the root partition to '
            'start the distribution update. Please ensure at least 5 GB '
            'is free. Distribution update will be retried after 24 hours,'
            ' if enabled.')
        Notification.update_or_create(id='upgrades-dist-upgrade-free-space',
                                      app_id='upgrades', severity='warning',
                                      title=title, message=message, actions=[{
                                          'type': 'dismiss'
                                      }], group='admin')
    elif 'started-dist-upgrade' in reason:
        logger.info('Started dist upgrade.')
        title = gettext_noop('Distribution update started')
        message = gettext_noop(
            'Started update to next stable release. This may take a long '
            'time to complete.')
        Notification.update_or_create(id='upgrades-dist-upgrade-started',
                                      app_id='upgrades', severity='info',
                                      title=title, message=message, actions=[{
                                          'type': 'dismiss'
                                      }], group='admin')
    else:
        logger.warning('Unhandled result of start-dist-upgrade: %s, %s',
                       dist_upgrade_started, reason)


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
    release, _ = get_current_release()
    if release == 'unstable' or (release == 'testing' and not cfg.develop):
        return False

    return True


def can_enable_dist_upgrade():
    """Return whether dist upgrade can be enabled."""
    release, _ = get_current_release()
    return release not in ['unstable', 'testing']


def can_test_dist_upgrade():
    """Return whether dist upgrade can be tested."""
    return can_enable_dist_upgrade() and cfg.develop


def test_dist_upgrade():
    """Test dist-upgrade from stable to testing."""
    if can_test_dist_upgrade():
        try_start_dist_upgrade(test=True)


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
