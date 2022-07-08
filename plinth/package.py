# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Framework for installing and updating distribution packages
"""

import enum
import json
import logging
import pathlib
import subprocess
import sys
import threading
from typing import Optional, Union

import apt.cache
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import actions, app
from plinth.errors import ActionError, MissingPackageError
from plinth.utils import format_lazy

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
            version: Optional[str] = None,  # ">=1.0,<2.0"
            distribution: Optional[str] = None,  # Debian, Ubuntu
            suite: Optional[str] = None,  # stable, testing
            codename: Optional[str] = None,  # bullseye-backports
            architecture: Optional[str] = None):  # arm64
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


class Packages(app.FollowerComponent):
    """Component to manage the packages of an app.

    This component is responsible for installation, upgrades and uninstallation
    of packages required by an app.
    """

    class ConflictsAction(enum.Enum):
        """Action to take when a conflicting package is installed."""
        IGNORE = 'ignore'  # Proceed as if there are no conflicts
        REMOVE = 'remove'  # Remove the packages before installing the app

    def __init__(self, component_id: str,
                 packages: list[Union[str, PackageExpression]],
                 skip_recommends: bool = False,
                 conflicts: Optional[list[str]] = None,
                 conflicts_action: Optional[ConflictsAction] = None):
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
        self.conflicts = conflicts
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
        # TODO: Drop the need for setup helper.
        module_name = self.app.__module__
        module = sys.modules[module_name]
        helper = module.setup_helper
        helper.install(self.get_actual_packages(),
                       skip_recommends=self.skip_recommends)

    def diagnose(self):
        """Run diagnostics and return results."""
        results = super().diagnose()
        cache = apt.Cache()
        for package_expression in self.package_expressions:
            try:
                package_name = package_expression.actual()
            except MissingPackageError:
                message = _('Package {expression} is not available for '
                            'install').format(expression=package_expression)
                results.append([message, 'failed'])
                continue

            result = 'warning'
            latest_version = '?'
            if package_name in cache:
                package = cache[package_name]
                latest_version = package.candidate.version
                if package.candidate.is_installed:
                    result = 'passed'

            message = _('Package {package_name} is the latest version '
                        '({latest_version})').format(
                            package_name=package_name,
                            latest_version=latest_version)
            results.append([message, result])

        return results

    def find_conflicts(self) -> Optional[list[str]]:
        """Return list of conflicting packages installed on the system."""
        if not self.conflicts:
            return None

        return packages_installed(self.conflicts)

    def has_unavailable_packages(self) -> Optional[bool]:
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


class PackageException(Exception):
    """A package operation has failed."""

    def __init__(self, error_string=None, error_details=None, *args, **kwargs):
        """Store apt-get error string and details."""
        super().__init__(*args, **kwargs)

        self.error_string = error_string
        self.error_details = error_details

    def __str__(self):
        """Return the strin representation of the exception."""
        return 'PackageException(error_string="{0}", error_details="{1}")' \
            .format(self.error_string, self.error_details)


class Transaction:
    """Information about an ongoing transaction."""

    def __init__(self, module_name, package_names):
        """Initialize transaction object.

        Set most values to None until they are sent as progress update.
        """
        self.module_name = module_name
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
            self._run_apt_command(['update'])
            extra_arguments = []
            if skip_recommends:
                extra_arguments.append('--skip-recommends')

            if force_configuration is not None:
                extra_arguments.append(
                    '--force-configuration={}'.format(force_configuration))

            if reinstall:
                extra_arguments.append('--reinstall')

            if force_missing_configuration:
                extra_arguments.append('--force-missing-configuration')

            self._run_apt_command(['install'] + extra_arguments +
                                  [self.module_name] + self.package_names)
        except subprocess.CalledProcessError as exception:
            logger.exception('Error installing package: %s', exception)
            raise

    def refresh_package_lists(self):
        """Refresh apt package lists."""
        try:
            self._run_apt_command(['update'])
        except subprocess.CalledProcessError as exception:
            logger.exception('Error updating package lists: %s', exception)
            raise

    def _run_apt_command(self, arguments):
        """Run apt-get and update progress."""
        self._reset_status()

        process = actions.superuser_run('packages', arguments,
                                        run_in_background=True)
        process.stdin.close()

        stdout_thread = threading.Thread(target=self._read_stdout,
                                         args=(process, ))
        stderr_thread = threading.Thread(target=self._read_stderr,
                                         args=(process, ))
        stdout_thread.start()
        stderr_thread.start()
        stdout_thread.join()
        stderr_thread.join()

        return_code = process.wait()
        if return_code != 0:
            raise PackageException(_('Error during installation'), self.stderr)

    def _read_stdout(self, process):
        """Read the stdout of the process and update progress."""
        for line in process.stdout:
            self._parse_progress(line.decode())

    def _read_stderr(self, process):
        """Read the stderr of the process and store in buffer."""
        self.stderr = process.stderr.read().decode()

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


def is_package_manager_busy():
    """Return whether a package manager is running."""
    try:
        actions.superuser_run('packages', ['is-package-manager-busy'],
                              log_error=False)
        return True
    except actions.ActionError:
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
    response = actions.superuser_run(
        'packages',
        ['filter-conffile-packages', '--packages'] + list(packages))
    return json.loads(response)


def packages_installed(candidates: Union[list, tuple]) -> list:
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


def remove(packages: Union[list, tuple]) -> None:
    """Remove packages."""
    try:
        actions.superuser_run('packages', ['remove', '--packages'] + packages)
    except ActionError:
        pass
