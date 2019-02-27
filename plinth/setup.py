#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Utilities for performing application setup operations.
"""

import logging
import os
import threading
import time
from collections import defaultdict

import apt

import plinth
from plinth.signals import post_setup

from . import package
from .errors import PackageNotInstalledError

logger = logging.getLogger(__name__)

_is_first_setup = False
is_first_setup_running = False
_is_shutting_down = False

_force_upgrader = None


class Helper(object):
    """Helper routines for modules to show progress."""

    def __init__(self, module_name, module):
        """Initialize the object."""
        self.module_name = module_name
        self.module = module
        self.current_operation = None
        self.is_finished = None
        self.exception = None
        self.allow_install = True

    def run_in_thread(self):
        """Execute the setup process in a thread."""
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        """Collect exceptions when running in a thread."""
        try:
            self.run()
        except Exception as exception:
            self.exception = exception

    def collect_result(self):
        """Return the exception if any."""
        exception = self.exception
        self.exception = None
        self.is_finished = None
        return exception

    def run(self, allow_install=True):
        """Execute the setup process."""
        # Setup for the module is already running
        if self.current_operation:
            return

        current_version = self.get_setup_version()
        if current_version >= self.module.version:
            return

        self.allow_install = allow_install
        self.exception = None
        self.current_operation = None
        self.is_finished = False
        try:
            if hasattr(self.module, 'setup'):
                logger.info('Running module setup - %s', self.module_name)
                self.module.setup(self, old_version=current_version)
            else:
                logger.info('Module does not require setup - %s',
                            self.module_name)
        except Exception as exception:
            logger.exception('Error running setup - %s', exception)
            raise exception
        else:
            self.set_setup_version(self.module.version)
            post_setup.send_robust(sender=self.__class__,
                                   module_name=self.module_name)
        finally:
            self.is_finished = True
            self.current_operation = None

    def install(self, package_names, skip_recommends=False,
                force_configuration=None):
        """Install a set of packages marking progress."""
        if self.allow_install is False:
            # Raise error if packages are not already installed.
            cache = apt.Cache()
            for package_name in package_names:
                if not cache[package_name].is_installed:
                    raise PackageNotInstalledError(package_name)

            return

        logger.info('Running install for module - %s, packages - %s',
                    self.module_name, package_names)

        transaction = package.Transaction(self.module_name, package_names)
        self.current_operation = {
            'step': 'install',
            'transaction': transaction,
        }
        transaction.install(skip_recommends, force_configuration)

    def call(self, step, method, *args, **kwargs):
        """Call an arbitrary method during setup and note down its stage."""
        logger.info('Running step for module - %s, step - %s',
                    self.module_name, step)
        self.current_operation = {'step': step}
        return method(*args, **kwargs)

    def get_state(self):
        """Return whether the module is not setup or needs upgrade."""
        current_version = self.get_setup_version()
        if current_version and self.module.version <= current_version:
            return 'up-to-date'

        # If a module need installing/updating but no setup method is
        # available, then automatically set version.
        #
        # Minor violation of 'get' only discipline for convenience.
        if not hasattr(self.module, 'setup'):
            self.set_setup_version(self.module.version)
            return 'up-to-date'

        if not current_version:
            return 'needs-setup'

        return 'needs-update'

    def get_setup_version(self):
        """Return the setup version of a module."""
        # XXX: Optimize version gets
        from . import models

        try:
            module_entry = models.Module.objects.get(pk=self.module_name)
            return module_entry.setup_version
        except models.Module.DoesNotExist:
            return 0

    def set_setup_version(self, version):
        """Set a module's setup version."""
        from . import models

        models.Module.objects.update_or_create(
            pk=self.module_name, defaults={'setup_version': version})

    def has_unavailable_packages(self):
        """Find if any of the packages managed by the module are not available.
        Returns True if one or more of the packages is not available in the
        user's Debian distribution or False otherwise.
        Returns None if it cannot be reliably determined whether the
        packages are available or not.
        """
        APT_LISTS_DIR = '/var/lib/apt/lists/'
        num_files = len([
            name for name in os.listdir(APT_LISTS_DIR)
            if os.path.isfile(os.path.join(APT_LISTS_DIR, name))
        ])
        if num_files < 2:  # not counting the lock file
            return None
        cache = apt.Cache()
        managed_pkgs = _get_module_managed_packages(self.module)
        unavailable_pkgs = (pkg_name for pkg_name in managed_pkgs
                            if pkg_name not in cache)
        return any(unavailable_pkgs)


def init(module_name, module):
    """Create a setup helper for a module for later use."""
    if not hasattr(module, 'setup_helper'):
        module.setup_helper = Helper(module_name, module)


def stop():
    """Set a flag to indicate that the setup process must stop."""
    global _is_shutting_down
    _is_shutting_down = True

    if _force_upgrader:
        _force_upgrader.shutdown()


def setup_modules(module_list=None, essential=False, allow_install=True):
    """Run setup on selected or essential modules."""
    logger.info(
        'Running setup for modules, essential - %s, '
        'selected modules - %s', essential, module_list)
    for module_name, module in plinth.module_loader.loaded_modules.items():
        if essential and not _is_module_essential(module):
            continue

        if module_list and module_name not in module_list:
            continue

        module.setup_helper.run(allow_install=allow_install)


def list_dependencies(module_list=None, essential=False):
    """Print list of packages required by selected or essential modules."""
    for module_name, module in plinth.module_loader.loaded_modules.items():
        if essential and not _is_module_essential(module):
            continue

        if module_list and module_name not in module_list and \
           '*' not in module_list:
            continue

        for package_name in _get_module_managed_packages(module):
            print(package_name)


def run_setup_in_background():
    """Run setup in a background thread."""
    _set_is_first_setup()
    threading.Thread(target=_run_setup).start()


def _run_setup():
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
    """Run setup on essential modules on first setup."""
    global is_first_setup_running
    is_first_setup_running = True
    # TODO When it errors out, show error in the UI
    run_setup_on_modules(None, allow_install=False)
    is_first_setup_running = False


def _run_regular_setup():
    """Run setup on all modules also installing required packages."""
    # TODO show notification that upgrades are running
    if package.is_package_manager_busy():
        raise Exception('Package manager is busy.')

    all_modules = _get_modules_for_regular_setup()
    run_setup_on_modules(all_modules, allow_install=True)


def _get_modules_for_regular_setup():
    all_modules = plinth.module_loader.loaded_modules.items()

    def is_setup_required(module):
        """Setup is required for:
        1. essential modules that are not up-to-date
        2. non-essential modules that are installed and need updates
        """
        if _is_module_essential(module) and \
           not _module_state_matches(module, 'up-to-date'):
            return True

        if _module_state_matches(module, 'needs-update'):
            return True

        return False

    return [name for name, module in all_modules if is_setup_required(module)]


def _is_module_essential(module):
    """Return if a module is an essential module."""
    return getattr(module, 'is_essential', False)


def _get_module_managed_packages(module):
    """Return list of packages managed by a module."""
    return getattr(module, 'managed_packages', [])


def _module_state_matches(module, state):
    """Return if the current setup state of a module matches given state."""
    return module.setup_helper.get_state() == state


def _set_is_first_setup():
    """Set whether all essential modules have been setup at least once."""
    global _is_first_setup
    modules = plinth.module_loader.loaded_modules.values()
    _is_first_setup = any((module for module in modules
                           if _is_module_essential(module)
                           and _module_state_matches(module, 'needs-setup')))


def run_setup_on_modules(module_list, allow_install=True):
    """Run setup on the given list of modules.

    module_list is the list of modules to run setup on. If None is given, run
    setup on all essential modules only.

    allow_install with or without package installation. When setting up
    essential modules, installing packages is not required as FreedomBox
    (Plinth) itself has dependencies on all essential modules.

    """
    try:
        if not module_list:
            setup_modules(essential=True, allow_install=allow_install)
        else:
            setup_modules(module_list, allow_install=allow_install)
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
    precautions need to be taken into account whenever relavent.

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
    - Package is not blacklisted.
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
    - Remove packages from blacklist
    - Remove packages unless in whitelist or whitelist is empty
    - Package in allowed origins
    - Don't consider packages that require restart (if configured).
    - Package dependencies satisfy origins, blacklist and whitelist.
    - Order packages alphabetically (order changes when upgrading in minimal
      steps).

    The upgrade process looks like:
    - Check for install while shutting down.
    - Check for dry run.
    - Mail list of changes.
    - Upgrade in minimal steps.
    - Clean downloaded packages.

    """

    _run_lock = threading.Lock()
    _wait_event = threading.Event()

    UPGRADE_ATTEMPTS = 12

    UPGRADE_ATTEMPT_WAIT_SECONDS = 30 * 60

    class TemporaryFailure(Exception):
        """Raised when upgrade fails but can be tried again immediately."""

    class PermanentFailure(Exception):
        """Raised when upgrade fails and there is nothing more we wish to do."""

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

        If we are actually upgrading packages, don nothing.
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

        if package.is_package_manager_busy():
            raise self.TemporaryFailure('Package manager is busy')

        apps = self._get_list_of_apps_to_force_upgrade()
        logger.info('Apps needing conffile upgrades: %s',
                    ', '.join([str(app.name) for app in apps]))

        need_retry = False
        for app, packages in apps.items():
            try:
                logger.info('Force upgrading app: %s', app.name)
                app.force_upgrade(app.setup_helper, packages)
                logger.info('Successfully force upgraded app: %s', app.name)
            except Exception as exception:
                logger.exception('Error running force upgrade: %s', exception)
                need_retry = True
                # Continue trying to upgrade other apps

        if need_retry:
            raise self.TemporaryFailure('Some apps failed to force upgrade.')

    def _get_list_of_apps_to_force_upgrade(self):
        """Return a list of app modules on which to run force upgrade."""
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

        apps = defaultdict(list)
        for package_name in conffile_packages:
            for app in package_apps_map[package_name]:
                apps[app].append(conffile_packages[package_name])

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
        for module in plinth.module_loader.loaded_modules.values():
            if not getattr(module, 'force_upgrade', None):
                # App does not implement force upgrade
                continue

            if not _module_state_matches(module, 'up-to-date'):
                # App is not installed.
                # Or needs an update, let it update first.
                continue

            managed_packages = _get_module_managed_packages(module)
            upgradable_packages.update(managed_packages)

            for managed_package in managed_packages:
                package_apps_map[managed_package].add(module)

        return upgradable_packages.intersection(
            set(packages)), package_apps_map


def on_package_cache_updated():
    """Called by D-Bus service when apt package cache is updated."""
    global _force_upgrader
    if not _force_upgrader:
        _force_upgrader = ForceUpgrader()

    _force_upgrader.on_package_cache_updated()
