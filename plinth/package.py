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

from django.utils.translation import ugettext as _
import logging

from plinth.utils import import_from_gi
glib = import_from_gi('GLib', '2.0')
packagekit = import_from_gi('PackageKitGlib', '1.0')


logger = logging.getLogger(__name__)
transactions = {}
packages_resolved = {}


class PackageException(Exception):
    """A package operation has failed."""

    def __init__(self, error_string=None, error_details=None, *args, **kwargs):
        """Store packagekit error string and details."""
        super(PackageException, self).__init__(*args, **kwargs)

        self.error_string = error_string
        self.error_details = error_details

    def __str__(self):
        """Return the strin representation of the exception."""
        return 'PackageException(error_string="{0}", error_details="{1}")' \
            .format(self.error_string, self.error_details)


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
        self.speed = None

    def get_id(self):
        """Return a identifier to use as a key in a map of transactions."""
        return frozenset(self.package_names)

    def __str__(self):
        """Return the string representation of the object"""
        return ('Transaction(packages={0}, allow_cancel={1}, status={2}, '
                ' percentage={3}, package={4}, item_progress={5})').format(
                    self.package_names, self.allow_cancel, self.status_string,
                    self.percentage, self.package, self.item_progress)

    def install(self):
        """Run a PackageKit transaction to install given packages."""
        try:
            self._do_install()
        except glib.Error as exception:
            raise PackageException(exception.message) from exception

    def _do_install(self):
        """Run a PackageKit transaction to install given packages.

        Raise exception in case of error.
        """
        client = packagekit.Client()
        client.set_interactive(False)

        # Refresh package cache from all enabled repositories
        results = client.refresh_cache(
            False, None, self.progress_callback, self)
        self._assert_success(results)

        # Resolve packages again to get the latest versions after refresh
        results = client.resolve(packagekit.FilterEnum.INSTALLED,
                                 tuple(self.package_names) + (None, ),
                                 None, self.progress_callback, self)
        self._assert_success(results)

        for package in results.get_package_array():
            packages_resolved[package.get_name()] = package

        package_ids = []
        for package_name in self.package_names:
            if package_name not in packages_resolved or \
               not packages_resolved[package_name]:
                raise PackageException(_('packages not found'))

            package_ids.append(packages_resolved[package_name].get_id())

        # Start package installation
        results = client.install_packages(
            packagekit.TransactionFlagEnum.ONLY_TRUSTED, package_ids + [None],
            None, self.progress_callback, self)
        self._assert_success(results)

    def _assert_success(self, results):
        """Check that the most recent operation was a success."""
        if results and results.get_error_code() is not None:
            error = results.get_error_code()
            error_code = error.get_code() if error else None
            error_string = packagekit.ErrorEnum.to_string(error_code) \
                if error_code else None
            error_details = error.get_details() if error else None
            raise PackageException(error_string, error_details)

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
        elif progress_type == packagekit.ProgressType.TRANSACTION_FLAGS:
            self.flags = progress.props.transaction_flags
        elif progress_type == packagekit.ProgressType.ROLE:
            self.role = progress.props.role
        elif progress_type == packagekit.ProgressType.CALLER_ACTIVE:
            self.caller_active = progress.props.caller_active
        elif progress_type == packagekit.ProgressType.DOWNLOAD_SIZE_REMAINING:
            self.download_size_remaining = \
                progress.props.download_size_remaining
        elif progress_type == packagekit.ProgressType.SPEED:
            self.speed = progress.props.speed
        else:
            logger.info('Unhandle packagekit progress callback - %s, %s',
                        progress, progress_type)
