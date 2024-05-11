# SPDX-License-Identifier: AGPL-3.0-or-later
"""Framework for installing and updating distribution packages."""

import enum
import logging
import pathlib
import time

import apt
import apt.cache
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, gettext_noop

import plinth.privileged.packages as privileged
from plinth import app as app_module
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)
from plinth.errors import MissingPackageError
from plinth.utils import format_lazy

from . import operation as operation_module
from .errors import PackageNotInstalledError

logger = logging.getLogger(__name__)


class PackageExpression:

    def possible(self) -> list[str]:
        """Return the list of possible packages before resolving."""
        raise NotImplementedError

    def actual(self) -> str:
        """Return the name of the package to install.

        TODO: Also return version and suite to install from.
        """
        raise NotImplementedError


class Package(PackageExpression):

    def __init__(
            self,
            name,
            optional: bool = False,
            version: str | None = None,  # ">=1.0,<2.0"
            distribution: str | None = None,  # Debian, Ubuntu
            suite: str | None = None,  # stable, testing
            codename: str | None = None,  # bullseye-backports
            architecture: str | None = None):  # arm64
        self.name = name
        self.optional = optional
        self.version = version
        self.distribution = distribution
        self.suite = suite
        self.codename = codename
        self.architecture = architecture

    def __repr__(self):
        return self.name

    def __or__(self, other):
        return PackageOr(self, other)

    def possible(self) -> list[str]:
        return [self.name]

    def actual(self) -> str:
        cache = apt.Cache()
        if self.name in cache:
            # TODO: Also return version and suite to install from
            return self.name

        raise MissingPackageError(self.name)


class PackageOr(PackageExpression):
    """Specify that one of the two packages will be installed."""

    def __init__(self, package1: PackageExpression,
                 package2: PackageExpression):
        self.package1 = package1
        self.package2 = package2

    def __repr__(self):
        return self.package1.name + ' | ' + self.package2.name

    def possible(self) -> list[str]:
        return self.package1.possible() + self.package2.possible()

    def actual(self) -> str:
        try:
            return self.package1.actual()
        except MissingPackageError:
            return self.package2.actual()


class Packages(app_module.FollowerComponent):
    """Component to manage the packages of an app.

    This component is responsible for installation, upgrades and uninstallation
    of packages required by an app.
    """

    class ConflictsAction(enum.Enum):
        """Action to take when a conflicting package is installed."""

        IGNORE = 'ignore'  # Proceed as if there are no conflicts
        REMOVE = 'remove'  # Remove the packages before installing the app

    def __init__(self, component_id: str,
                 packages: list[str | PackageExpression],
                 skip_recommends: bool = False,
                 conflicts: list[str] | None = None,
                 conflicts_action: ConflictsAction | None = None):
        """Initialize a new packages component.

        'component_id' should be a unique ID across all components of an app
        and across all components.

        'packages' is the list of Debian packages managed by this component.

        'skip_recommends' is a boolean specifying whether recommended packages
        should be installed along with the listed packages.

        'conflicts' is the list of Debian packages that can't simultaneously be
        installed with packages listed here. None if there are no known
        conflicting packages.

        'conflicts_action' is a string representing the action to take when it
        is found that conflicting Debian packages are installed on the system.
        None if there are no known conflicting packages.
        """
        super().__init__(component_id)

        self.component_id = component_id
        self._packages: list[PackageExpression] = []
        for package in packages:
            if isinstance(package, str):
                self._packages.append(Package(package))
            else:
                self._packages.append(package)

        self.skip_recommends = skip_recommends
        self.conflicts = conflicts or []
        self.conflicts_action = conflicts_action

    @property
    def package_expressions(self) -> list[PackageExpression]:
        """Return the list of managed packages as expressions."""
        return self._packages

    @property
    def possible_packages(self) -> list[str]:
        """Return the list of possible packages before resolving."""
        packages: list[str] = []
        for package_expression in self.package_expressions:
            packages.extend(package_expression.possible())

        return packages

    def get_actual_packages(self) -> list[str]:
        """Return the computed list of packages to install.

        Raise MissingPackageError if a required package is not available.
        """
        return [
            package_expression.actual()
            for package_expression in self.package_expressions
        ]

    def setup(self, old_version):
        """Install the packages."""
        packages_to_remove = self.find_conflicts()
        if packages_to_remove and \
           self.conflicts_action not in (None, self.ConflictsAction.IGNORE):
            logger.info('Removing conflicting packages: %s',
                        packages_to_remove)
            uninstall(packages_to_remove, purge=False)

        install(self.get_actual_packages(),
                skip_recommends=self.skip_recommends)

    def uninstall(self):
        """Uninstall and purge the packages."""
        # Ensure package list is update-to-date before looking at dependencies.
        refresh_package_lists()

        # List of packages to purge from the system
        packages = self.get_actual_packages()
        logger.info('App\'s list of packages to remove: %s', packages)

        packages = self._filter_packages_to_keep(packages)
        uninstall(packages, purge=True)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return results."""
        results = super().diagnose()
        cache = apt.Cache()
        for package_expression in self.package_expressions:
            try:
                package_name = package_expression.actual()
            except MissingPackageError:
                check_id = f'package-available-{package_expression}'
                description = gettext_noop('Package {package_expression} is '
                                           'not available for install')
                parameters: DiagnosticCheckParameters = {
                    'package_expression': str(package_expression)
                }
                results.append(
                    DiagnosticCheck(check_id, description, Result.FAILED,
                                    parameters, self.component_id))
                continue

            result = Result.WARNING
            latest_version = '?'
            if package_name in cache:
                package = cache[package_name]
                if package.candidate:
                    latest_version = package.candidate.version
                    if package.candidate.is_installed:
                        result = Result.PASSED

            check_id = f'package-latest-{package_name}'
            description = gettext_noop('Package {package_name} is the latest '
                                       'version ({latest_version})')
            parameters = {
                'package_name': str(package_name),
                'latest_version': str(latest_version)
            }
            results.append(
                DiagnosticCheck(check_id, description, result, parameters,
                                self.component_id))

        return results

    def find_conflicts(self) -> list[str] | None:
        """Return list of conflicting packages installed on the system."""
        if not self.conflicts:
            return None

        return packages_installed(self.conflicts)

    def has_unavailable_packages(self) -> bool | None:
        """Return whether any of the packages are not available.

        Returns True if one or more of the packages is not available in the
        user's Debian distribution or False otherwise. Returns None if it
        cannot be reliably determined whether the packages are available or
        not.
        """
        apt_lists_dir = pathlib.Path('/var/lib/apt/lists/')
        num_files = len(
            [child for child in apt_lists_dir.iterdir() if child.is_file()])
        if num_files < 2:  # not counting the lock file
            return None

        # List of all packages from all Package components
        try:
            self.get_actual_packages()
        except MissingPackageError:
            return True

        return False

    def _filter_packages_to_keep(self, packages: list[str]) -> list[str]:
        """Filter out the list of packages to keep from given list.

        Packages to keep are packages needed by other installed apps and their
        dependencies (PreDepends, Depends, Recommends).
        """
        packages_set: set[str] = set(packages)

        # Get list of packages needed by other installed apps (packages to
        # keep).
        keep_packages: set[str] = set()
        for app in app_module.App.list():
            # uninstall() will be called on Packages of this app separately
            # for uninstalling this app.
            if app == self.app:
                continue

            if app.get_setup_state() == app_module.App.SetupState.NEEDS_SETUP:
                continue

            # Remove packages used by other installed apps
            for component in app.get_components_of_type(Packages):
                keep_packages |= set(component.get_actual_packages())

        # Get list of all the dependencies of packages to keep.
        keep_packages_with_deps: set[str] = set()
        cache = apt.Cache()
        while keep_packages:
            package_name = keep_packages.pop()
            if package_name in keep_packages_with_deps:
                continue  # Already processed

            keep_packages_with_deps.add(package_name)
            if package_name not in cache:
                continue  # Package is not available in sources

            if not cache[package_name].is_installed:
                continue  # Package is not installed

            version = cache[package_name].installed
            if not version:
                continue

            dependencies = version.dependencies + version.recommends
            for dependency in dependencies:
                for or_dependency in dependency.or_dependencies:
                    keep_packages.add(or_dependency.name)

        # Filter out any packages that are to be kept or their dependencies.
        packages_set -= keep_packages_with_deps

        # Preserve order of packages for ease of testing.
        return [package for package in packages if package in packages_set]


class PackageException(Exception):
    """A package operation has failed."""


class Transaction:
    """Information about an ongoing transaction."""

    def __init__(self, app_id, package_names):
        """Initialize transaction object.

        Set most values to None until they are sent as progress update.
        """
        self.app_id = app_id
        self.package_names = package_names

        self._reset_status()

    def get_id(self):
        """Return a identifier to use as a key in a map of transactions."""
        return frozenset(self.package_names)

    def _reset_status(self):
        """Reset the current status progress."""
        self.status_string = ''
        self.percentage = 0
        self.stderr = None

    def install(self, skip_recommends=False, force_configuration=None,
                reinstall=False, force_missing_configuration=False):
        """Run an apt-get transaction to install given packages.

        If force_configuration is set to 'new', dpkg options will be enabled to
        make it force overwrite (without prompts) new configuration in place of
        old configuration (with a backup). This is useful when writing
        migration scripts in FreedomBox to handle the upgrades when
        unattended-upgrades refuse to upgrade a package due to configuration
        prompts.

        If force_configuration is set to 'old', dpkg options will be enabled to
        make it keep the old configuration (without prompts). This is useful
        when the Debian packages introduce new configuration with just
        cosmetics (such as updates to comments) and keeping the old
        configuration has same semantics.

        If force_configuration is None, no special options are passed to
        apt/dpkg for configuration file behavior.

        If reinstall is True, packages will be reinstalled, even if they are
        the latest version.

        If force_missing_configuration is True, any configuration files that
        have been removed after the first package has been installed will be
        restored.

        """
        try:
            privileged.update()
            kwargs = {
                'app_id': self.app_id,
                'packages': self.package_names,
                'skip_recommends': skip_recommends,
                'force_configuration': force_configuration,
                'reinstall': reinstall,
                'force_missing_configuration': force_missing_configuration
            }
            privileged.install(**kwargs)
        except Exception as exception:
            logger.exception('Error installing package: %s', exception)
            raise

    def uninstall(self, purge):
        """Run an apt-get transaction to uninstall given packages."""
        try:
            privileged.remove(app_id=self.app_id, packages=self.package_names,
                              purge=purge)
        except Exception as exception:
            logger.exception('Error uninstalling package: %s', exception)
            raise

    def refresh_package_lists(self):
        """Refresh apt package lists."""
        try:
            privileged.update()
        except Exception as exception:
            logger.exception('Error updating package lists: %s', exception)
            raise

    def _parse_progress(self, line):
        """Parse the apt-get process output line.

        See README.progress-reporting in apt source code.
        """
        parts = line.split(':')
        if len(parts) < 4:
            return

        status_map = {
            'pmstatus':
                gettext_lazy('installing'),
            'dlstatus':
                gettext_lazy('downloading'),
            'media-change':
                gettext_lazy('media change'),
            'pmconffile':
                format_lazy(gettext_lazy('configuration file: {file}'),
                            file=parts[1]),
        }
        self.status_string = status_map.get(parts[0], '')
        self.percentage = int(float(parts[2]))


def install(package_names, skip_recommends=False, force_configuration=None,
            reinstall=False, force_missing_configuration=False):
    """Install a set of packages marking progress."""
    try:
        operation = operation_module.Operation.get_operation()
    except AttributeError:
        raise RuntimeError(
            'install() must be called from within an operation.')

    if not operation.thread_data.get('allow_install', True):
        # Raise error if packages are not already installed.
        cache = apt.Cache()
        for package_name in package_names:
            if not cache[package_name].is_installed:
                raise PackageNotInstalledError(package_name)

        return

    start_time = time.time()
    while is_package_manager_busy():
        if time.time() - start_time >= 24 * 3600:  # One day
            raise PackageException(_('Timeout waiting for package manager'))

        time.sleep(3)  # seconds

    logger.info('Running install for app - %s, packages - %s',
                operation.app_id, package_names)

    from . import package
    transaction = package.Transaction(operation.app_id, package_names)
    operation.thread_data['transaction'] = transaction
    transaction.install(skip_recommends, force_configuration, reinstall,
                        force_missing_configuration)


def uninstall(package_names, purge):
    """Uninstall a set of packages."""
    try:
        operation = operation_module.Operation.get_operation()
    except AttributeError:
        raise RuntimeError(
            'uninstall() must be called from within an operation.')

    start_time = time.time()
    while is_package_manager_busy():
        if time.time() - start_time >= 24 * 3600:  # One day
            raise PackageException(_('Timeout waiting for package manager'))

        time.sleep(3)  # seconds

    logger.info('Running uninstall for app - %s, packages - %s',
                operation.app_id, package_names)

    from . import package
    transaction = package.Transaction(operation.app_id, package_names)
    operation.thread_data['transaction'] = transaction
    transaction.uninstall(purge)


def is_package_manager_busy():
    """Return whether a package manager is running."""
    try:
        return privileged.is_package_manager_busy(_log_error=False)
    except Exception:
        return False


def refresh_package_lists():
    """To be run in case apt package lists are outdated."""
    transaction = Transaction(None, None)
    transaction.refresh_package_lists()


def filter_conffile_prompt_packages(packages):
    """Return a filtered info on packages that require conffile prompts.

    Information for each package includes: current_version, new_version and
    list of modified_conffiles.
    """
    return privileged.filter_conffile_packages(list(packages))


def packages_installed(candidates: list | tuple) -> list:
    """Check which candidates are installed on the system.

    :param candidates: A list of package names.
    :return: A list of installed Debian package names.
    """
    cache = apt.cache.Cache()
    installed_packages = []
    for package_name in candidates:
        try:
            package = cache[package_name]
            if package.is_installed:
                installed_packages.append(package_name)
        except KeyError:
            pass

    return installed_packages
