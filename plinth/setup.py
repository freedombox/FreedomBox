# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Utilities for performing application setup operations.
"""

import logging
import threading
import time
from collections import defaultdict

import apt
from django.utils.translation import gettext_noop

import plinth
from plinth import app as app_module
from plinth.package import PackageException, Packages
from plinth.signals import post_setup

from . import operation as operation_module
from . import package
from .privileged import packages as packages_privileged

logger = logging.getLogger(__name__)

_is_first_setup = False
is_first_setup_running = False
_is_shutting_down = False


def run_setup_on_app(app_id, allow_install=True, rerun=False):
    """Execute the setup process in a thread."""
    # App is already up-to-date
    app = app_module.App.get(app_id)
    current_version = app.get_setup_version()
    if not rerun and current_version >= app.info.version:
        return

    if not current_version:
        name = gettext_noop('Installing app')
    else:
        name = gettext_noop('Updating app')

    logger.debug('Creating operation to setup app: %s', app_id)
    show_notification = show_message = (current_version
                                        or not app.info.is_essential)
    return operation_module.manager.new(
        f'{app_id}-setup', app_id, name, _run_setup_on_app,
        [app, current_version], show_message=show_message,
        show_notification=show_notification,
        thread_data={'allow_install': allow_install})


def _run_setup_on_app(app, current_version):
    """Execute the setup process."""
    logger.info('Setup run: %s', app.app_id)
    exception_to_update = None
    message = None
    try:
        force_upgrader = ForceUpgrader.get_instance()

        # Check if this app needs force_upgrade. If it is needed, but not yet
        # supported for the new version of the package, then an exception will
        # be raised, so that we do not run setup.
        force_upgrader.attempt_upgrade_for_app(app.app_id)

        current_version = app.get_setup_version()
        app.setup(old_version=current_version)
        app.set_setup_version(app.info.version)
        post_setup.send_robust(sender=app.__class__, module_name=app.app_id)
    except PackageException as exception:
        exception_to_update = exception
        error_string = getattr(exception, 'error_string', str(exception))
        error_details = getattr(exception, 'error_details', '')
        if not current_version:
            message = gettext_noop('Error installing app: {string} '
                                   '{details}').format(string=error_string,
                                                       details=error_details)
        else:
            message = gettext_noop('Error updating app: {string} '
                                   '{details}').format(string=error_string,
                                                       details=error_details)
    except Exception as exception:
        exception_to_update = exception
        if not current_version:
            message = gettext_noop('Error installing app: {error}').format(
                error=exception)
        else:
            message = gettext_noop('Error updating app: {error}').format(
                error=exception)
    else:
        if not current_version:
            message = gettext_noop('App installed.')
        else:
            message = gettext_noop('App updated')

    logger.info('Setup completed: %s: %s %s', app.app_id, message,
                exception_to_update)
    operation = operation_module.Operation.get_operation()
    operation.on_update(message, exception_to_update)


def run_uninstall_on_app(app_id):
    """Execute the uninstall process in a thread."""
    # App is already uninstalled
    app = app_module.App.get(app_id)
    if not app.get_setup_version():
        return

    logger.debug('Creating operation to uninstall app: %s', app_id)
    return operation_module.manager.new(f'{app_id}-uninstall', app_id,
                                        gettext_noop('Uninstalling app'),
                                        _run_uninstall_on_app, [app],
                                        show_notification=True)


def _run_uninstall_on_app(app):
    """Execute the uninstall process."""
    logger.info('Uninstall run: %s', app.app_id)
    exception_to_update = None
    message = None
    try:
        app.disable()
        app.uninstall()
        app.set_setup_version(0)
    except PackageException as exception:
        exception_to_update = exception
        error_string = getattr(exception, 'error_string', str(exception))
        error_details = getattr(exception, 'error_details', '')
        message = gettext_noop('Error uninstalling app: {string} '
                               '{details}').format(string=error_string,
                                                   details=error_details)

    except Exception as exception:
        exception_to_update = exception
        message = gettext_noop('Error uninstalling app: {error}').format(
            error=exception)
    else:
        message = gettext_noop('App uninstalled.')

    logger.info('Uninstall completed: %s: %s %s', app.app_id, message,
                exception_to_update)
    operation = operation_module.Operation.get_operation()
    operation.on_update(message, exception_to_update)


def stop():
    """Set a flag to indicate that the setup process must stop."""
    global _is_shutting_down
    _is_shutting_down = True

    force_upgrader = ForceUpgrader.get_instance()
    force_upgrader.shutdown()


def setup_apps(app_ids=None, essential=False, allow_install=True):
    """Run setup on selected or essential apps."""
    logger.info(
        'Running setup for apps, essential - %s, '
        'selected apps - %s', essential, app_ids)
    for app in app_module.App.list():
        if essential and not app.info.is_essential:
            continue

        if app_ids and app.app_id not in app_ids:
            continue

        operation = run_setup_on_app(app.app_id, allow_install=allow_install)
        if operation:
            operation.join()


def list_dependencies(app_ids=None, essential=False):
    """Print list of packages required by selected or essential apps."""
    for app in app_module.App.list():
        if essential and not app.info.is_essential:
            continue

        if app_ids and app.app_id not in app_ids and \
           '*' not in app_ids:
            continue

        for component in app.get_components_of_type(Packages):
            for package_expression in component.package_expressions:
                print(package_expression)


def run_setup_in_background():
    """Run setup in a background thread."""
    _set_is_first_setup()
    threading.Thread(target=_run_setup_on_startup).start()


def _run_setup_on_startup():
    """Run setup with retry till it succeeds."""
    sleep_time = 10
    while True:
        try:
            if _is_first_setup:
                logger.info('Running first setup.')
                _run_first_setup()
                break
            else:
                logger.info('Running regular setup.')
                _run_regular_setup()
                break
        except Exception as ex:
            logger.warning('Unable to complete setup: %s', ex)
            logger.info('Will try again in {} seconds'.format(sleep_time))
            time.sleep(sleep_time)
            if _is_shutting_down:
                break

    logger.info('Setup thread finished.')


def _run_first_setup():
    """Run setup on essential apps on first setup."""
    global is_first_setup_running
    is_first_setup_running = True
    run_setup_on_apps(None, allow_install=False)
    is_first_setup_running = False


def _run_regular_setup():
    """Run setup on all apps also installing required packages."""
    app_ids = _get_apps_for_regular_setup()
    run_setup_on_apps(app_ids, allow_install=True)


def _get_apps_for_regular_setup():

    def is_setup_required(app):
        """Setup is required for:
        1. essential apps that are not up-to-date
        2. non-essential app that are installed and need updates
        """
        if (app.info.is_essential and app.get_setup_state()
                != app_module.App.SetupState.UP_TO_DATE):
            return True

        if app.get_setup_state() == app_module.App.SetupState.NEEDS_UPDATE:
            return True

        return False

    return [
        app.app_id for app in app_module.App.list() if is_setup_required(app)
    ]


def _set_is_first_setup():
    """Set whether all essential apps have been setup at least once."""
    global _is_first_setup
    _is_first_setup = any((app for app in app_module.App.list()
                           if app.info.is_essential and app.needs_setup()))


def run_setup_on_apps(app_ids, allow_install=True):
    """Run setup on the given list of apps.

    apps is the list of apps to run setup on. If None is given, run setup on
    all essential apps only.

    allow_install with or without package installation. When setting up
    essential apps, installing packages is not required as FreedomBox
    (Plinth) itself has dependencies on all essential apps.

    """
    try:
        if not app_ids:
            setup_apps(essential=True, allow_install=allow_install)
        else:
            setup_apps(app_ids, allow_install=allow_install)
    except Exception as exception:
        logger.error('Error running setup - %s', exception)
        raise


class ForceUpgrader():
    """Find and upgrade packages by force when conffile prompt is needed.

    Primary duty here is take responsibility of packages that will be rejected
    by unattended-upgrades for upgrades. Only packages that apps manage are
    handled as that is only case in which we know how to deal with
    configuration file changes. Roughly, we will read old configuration file,
    force upgrade the package with new configuration and then apply the old
    preferences on it.

    When upgrades packages, many things have to be kept in mind. The following
    is the understanding on how unattended-upgrades does its upgrades. These
    precautions need to be taken into account whenever relevant.

    Checks done by unattended upgrades before upgrading:
    - Check if today is a configured patch day.
    - Check if running on development release.
    - Cache does not have broken packages.
    - Whether system (and hence this process itself) is shutting down.
    - System is on AC Power (if configured).
    - Whether system is on a metered connection.
    - Package system is locked.
    - Check if dpkg journal is dirty and fix it.
    - Take care that upgrade process does not terminate/crash self.
    - Check if cache has broken dependencies.
    - Remove auto removable packages.
    - Download all packages before upgrade
    - Perform conffile prompt checks
      - Ignore if dpkg options has --force-confold or --force-confnew

    Unattended upgrades checks for configuration file prompts as follows:
    - Package downloaded successfully.
    - Package is complete.
    - File is available.
    - Package is trusted.
    - Package is not in denylist.
    - Package extension is .deb.
    - Get conffiles values from control data of .deb.
    - Read from /var/lib/dpkg/status, Package and Conffiles section.
    - Read each conffile from system and compute md5sum.
    - If new package md5sum == dpkg status md5 == file's md5 then no conffile
      prompt.
    - If conffiles in new package not found in dpkg status but found on system
      with different md5sum, conffile prompt is available.

    Filtering of packages to upgrade is done as follows:
    - Packages is upgradable.
    - Remove packages from denylist
    - Remove packages unless in allowlist or allowlist is empty
    - Package in allowed origins
    - Don't consider packages that require restart (if configured).
    - Package dependencies satisfy origins, denylist and allowlist.
    - Order packages alphabetically (order changes when upgrading in minimal
      steps).

    The upgrade process looks like:
    - Check for install while shutting down.
    - Check for dry run.
    - Mail list of changes.
    - Upgrade in minimal steps.
    - Clean downloaded packages.

    """

    _instance = None
    _run_lock = threading.Lock()
    _wait_event = threading.Event()

    UPGRADE_ATTEMPTS = 12

    UPGRADE_ATTEMPT_WAIT_SECONDS = 30 * 60

    class TemporaryFailure(Exception):
        """Raised when upgrade fails but can be tried again immediately."""

    class PermanentFailure(Exception):
        """Raised when upgrade fails and there is nothing more we wish to do.
        """

    @classmethod
    def get_instance(cls):
        """Return a single instance of a the class."""
        if not cls._instance:
            cls._instance = ForceUpgrader()

        return cls._instance

    def __init__(self):
        """Initialize the force upgrader."""
        if plinth.cfg.develop:
            self.UPGRADE_ATTEMPT_WAIT_SECONDS = 10

    def on_package_cache_updated(self):
        """Trigger upgrades when notified about changes to package cache.

        Call the upgrade process guaranteeing that it will not run more than
        once simultaneously.

        """
        if not self._run_lock.acquire(blocking=False):
            logger.info('Package upgrade already in process')
            return

        try:
            self._run_upgrade()
        finally:
            self._run_lock.release()

    def _run_upgrade(self):
        """Attempt the upgrade process multiple times.

        This method is guaranteed to not to run more than once simultaneously.

        """
        for _ in range(self.UPGRADE_ATTEMPTS):
            logger.info('Waiting for %s seconds before attempting upgrade',
                        self.UPGRADE_ATTEMPT_WAIT_SECONDS)
            if self._wait_event.wait(self.UPGRADE_ATTEMPT_WAIT_SECONDS):
                logger.info('Stopping upgrade attempts due to shutdown')
                return

            try:
                logger.info('Attempting to perform upgrade')
                self._attempt_upgrade()
                return
            except self.TemporaryFailure as exception:
                logger.info('Cannot perform upgrade now: %s', exception)
            except self.PermanentFailure as exception:
                logger.error('Upgrade failed: %s', exception)
                return
            except Exception as exception:
                # Assume all other errors are temporary
                logger.exception('Unknown exception: %s', exception)

        logger.info('Giving up on upgrade after too many retries')

    def shutdown(self):
        """If we are sleeping for next attempt, cancel it.

        If we are actually upgrading packages, do nothing.
        """
        self._wait_event.set()

    def _attempt_upgrade(self):
        """Attempt to perform an upgrade.

        Raise TemporaryFailure if upgrade can't be performed now.

        Raise PermanentFailure if upgrade can't be performed until something
        with the system state changes. We don't want to try again until
        notified of further package cache changes.

        Return nothing otherwise.

        """
        if _is_shutting_down:
            raise self.PermanentFailure('Service is shutting down')

        if packages_privileged.is_package_manager_busy():
            raise self.TemporaryFailure('Package manager is busy')

        apps = self._get_list_of_apps_to_force_upgrade()
        logger.info(
            'Apps needing conffile upgrades: %s', ', '.join(
                [str(app_module.App.get(app_id).info.name) for app_id in apps])
            or 'None')

        need_retry = False
        for app_id, packages in apps.items():
            app = app_module.App.get(app_id)
            try:
                logger.info('Force upgrading app: %s', app.info.name)
                if self._run_force_upgrade_as_operation(app, packages):
                    logger.info('Successfully force upgraded app: %s',
                                app.info.name)
                else:
                    logger.info('Ignored force upgrade for app: %s',
                                app.info.name)
            except Exception as exception:
                logger.exception('Error running force upgrade: %s', exception)
                need_retry = True
                # Continue trying to upgrade other apps

        if need_retry:
            raise self.TemporaryFailure('Some apps failed to force upgrade.')

    def attempt_upgrade_for_app(self, app_id):
        """Attempt to perform an upgrade for specified app.

        Raise TemporaryFailure if upgrade can't be performed now.

        Raise PermanentFailure if upgrade can't be performed until something
        with the system state changes. We don't want to try again until
        notified of further package cache changes.

        Return True if upgrade was performed successfully.

        Return False if upgrade is not needed.

        """
        if _is_shutting_down:
            raise self.PermanentFailure('Service is shutting down')

        if packages_privileged.is_package_manager_busy():
            raise self.TemporaryFailure('Package manager is busy')

        apps = self._get_list_of_apps_to_force_upgrade()
        if app_id not in apps:
            logger.info('App %s does not need force upgrade', app_id)
            return False

        packages = apps[app_id]
        app = app_module.App.get(app_id)
        try:
            logger.info('Force upgrading app: %s', app.info.name)
            if app.force_upgrade(packages):
                logger.info('Successfully force upgraded app: %s',
                            app.info.name)
                return True
            else:
                logger.warning('Ignored force upgrade for app: %s',
                               app.info.name)
                raise self.TemporaryFailure(
                    'Force upgrade is needed, but not yet implemented for new '
                    f'version of app: {app_id}')
        except Exception as exception:
            logger.exception('Error running force upgrade: %s', exception)
            raise self.TemporaryFailure(
                f'App {app_id} failed to force upgrade.')

    def _run_force_upgrade_as_operation(self, app, packages):
        """Start an operation for force upgrading."""
        name = gettext_noop('Updating app packages')
        operation = operation_module.manager.new(f'{app.app_id}-force-upgrade',
                                                 app.app_id, name,
                                                 app.force_upgrade, [packages],
                                                 show_message=False,
                                                 show_notification=False)
        return operation.join()  # Wait for completion, raise Exception

    def _get_list_of_apps_to_force_upgrade(self):
        """Return a list of app on which to run force upgrade."""
        packages = self._get_list_of_upgradable_packages()
        if not packages:  # No packages to upgrade
            return {}

        package_names = [package.name for package in packages]
        logger.info('Packages available for upgrade: %s',
                    ', '.join(package_names))

        managed_packages, package_apps_map = self._filter_managed_packages(
            package_names)
        if not managed_packages:
            return {}

        conffile_packages = package.filter_conffile_prompt_packages(
            managed_packages)
        logger.info('Packages that need conffile upgrades: %s',
                    conffile_packages)

        apps = defaultdict(dict)
        for package_name in conffile_packages:
            for app_id in package_apps_map[package_name]:
                apps[app_id][package_name] = conffile_packages[package_name]

        return apps

    @staticmethod
    def _get_list_of_upgradable_packages():
        """Return list of packages that can be upgraded."""
        cache = apt.cache.Cache()
        return [package for package in cache if package.is_upgradable]

    @staticmethod
    def _filter_managed_packages(packages):
        """Filter out packages that apps don't force upgrade.

        Return packages in the list that are managed by at least one app that
        can perform force upgrade.

        """
        package_apps_map = defaultdict(set)
        upgradable_packages = set()
        for app in app_module.App.list():
            if not getattr(app, 'force_upgrade', None):
                # App does not implement force upgrade
                continue

            if (app.get_setup_state() != app_module.App.SetupState.UP_TO_DATE):
                # App is not installed.
                # Or needs an update, let it update first.
                continue

            for component in app.get_components_of_type(Packages):
                upgradable_packages.update(component.possible_packages)

                for managed_package in component.possible_packages:
                    package_apps_map[managed_package].add(app.app_id)

        return upgradable_packages.intersection(
            set(packages)), package_apps_map


def on_package_cache_updated():
    """Called by D-Bus service when apt package cache is updated."""
    force_upgrader = ForceUpgrader.get_instance()
    force_upgrader.on_package_cache_updated()
