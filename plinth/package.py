#
# This file is part of Plinth.
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
Framework for installing and updating distribution packages
"""

import functools
from gi.repository import PackageKitGlib as packagekit
import logging
import threading

import plinth


logger = logging.getLogger(__name__)
transactions = {}
packages_resolved = {}


class Transaction(object):
    """Information about an ongoing transaction."""

    def __init__(self, package_names):
        """Initialize transaction object.

        Set most values to None until they are sent as progress update.
        """
        self.package_names = package_names

        # Progress
        self.allow_cancel = None
        self.percentage = None
        self.status = None
        self.status_string = None
        self.flags = None
        self.package = None
        self.package_id = None
        self.item_progress = None
        self.role = None
        self.caller_active = None
        self.download_size_remaining = None

    def get_id(self):
        """Return a identifier to use as a key in a map of transactions."""
        return frozenset(self.package_names)

    def __str__(self):
        """Return the string representation of the object"""
        return ('Transaction(packages={0}, allow_cancel={1}, status={2}, '
                ' percentage={3}, package={4}, item_progress={5})').format(
                    self.package_names, self.allow_cancel, self.status_string,
                    self.percentage, self.package, self.item_progress)

    def start_install(self):
        """Start a PackageKit transaction to install given list of packages.

        This operation is non-blocking at it spawns a new thread.
        """
        thread = threading.Thread(target=self._install)
        thread.start()

    def _install(self):
        """Run a PackageKit transaction to install given packages."""
        package_ids = [packages_resolved[package_name].get_id()
                       for package_name in self.package_names]
        client = packagekit.Client()
        client.set_interactive(False)
        client.install_packages(packagekit.TransactionFlagEnum.ONLY_TRUSTED,
                                package_ids + [None], None,
                                self.progress_callback, self)

    def progress_callback(self, progress, progress_type, user_data):
        """Process progress updates on package resolve operation"""
        if progress_type == packagekit.ProgressType.PERCENTAGE:
            self.percentage = progress.props.percentage
        elif progress_type == packagekit.ProgressType.PACKAGE:
            self.package = progress.props.package
        elif progress_type == packagekit.ProgressType.ALLOW_CANCEL:
            self.allow_cancel = progress.props.allow_cancel
        elif progress_type == packagekit.ProgressType.PACKAGE_ID:
            self.package_id = progress.props.package_id
        elif progress_type == packagekit.ProgressType.ITEM_PROGRESS:
            self.item_progress = progress.props.item_progress
        elif progress_type == packagekit.ProgressType.STATUS:
            self.status = progress.props.status
            self.status_string = \
                packagekit.StatusEnum.to_string(progress.props.status)
            if self.status == packagekit.StatusEnum.FINISHED:
                self.finish()
        elif progress_type == packagekit.ProgressType.TRANSACTION_FLAGS:
            self.flags = progress.props.transaction_flags
        elif progress_type == packagekit.ProgressType.ROLE:
            self.role = progress.props.role
        elif progress_type == packagekit.ProgressType.CALLER_ACTIVE:
            self.caller_active = progress.props.caller_active
        elif progress_type == packagekit.ProgressType.DOWNLOAD_SIZE_REMAINING:
            self.download_size_remaining = \
                progress.props.download_size_remaining
        else:
            logger.info('Unhandle packagekit progress callback - %s, %s',
                        progress, progress_type)

    def finish(self):
        """Perform clean up operations on the transaction.

        Remove self from global transactions list.
        """
        del transactions[self.get_id()]


def required(*package_names):
    """Decorate a view to check and install required packages."""

    def wrapper2(func):
        """Return a function to check and install packages."""

        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            """Check and install packages required by a view."""
            if not is_installing(package_names) and \
               check_installed(package_names):
                return func(request, *args, **kwargs)

            view = plinth.views.PackageInstallView.as_view()
            return view(request, package_names=package_names, *args, **kwargs)

        return wrapper

    return wrapper2


def check_installed(package_names):
    """Return a boolean installed status of package.

    This operation is blocking and waits until the check is finished.
    """
    def _callback(progress, progress_type, user_data):
        """Process progress updates on package resolve operation."""
        pass

    client = packagekit.Client()
    response = client.resolve(packagekit.FilterEnum.INSTALLED,
                              package_names + (None, ), None,
                              _callback, None)

    installed_package_names = []
    for package in response.get_package_array():
        if package.get_info() == packagekit.InfoEnum.INSTALLED:
            installed_package_names.append(package.get_name())

        packages_resolved[package.get_name()] = package

    return set(installed_package_names) == set(package_names)


def is_installing(package_names):
    """Return whether a set of packages are currently being installed."""
    return frozenset(package_names) in transactions


def start_install(package_names):
    """Start a PackageKit transaction to install given list of packages.

    This operation is non-blocking at it spawns a new thread.
    """
    transaction = Transaction(package_names)
    transactions[frozenset(package_names)] = transaction

    transaction.start_install()
