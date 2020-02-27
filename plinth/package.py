# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Framework for installing and updating distribution packages
"""

import json
import logging
import subprocess
import threading

from django.utils.translation import ugettext as _

from plinth import actions

logger = logging.getLogger(__name__)


class PackageException(Exception):
    """A package operation has failed."""
    def __init__(self, error_string=None, error_details=None, *args, **kwargs):
        """Store apt-get error string and details."""
        super(PackageException, self).__init__(*args, **kwargs)

        self.error_string = error_string
        self.error_details = error_details

    def __str__(self):
        """Return the strin representation of the exception."""
        return 'PackageException(error_string="{0}", error_details="{1}")' \
            .format(self.error_string, self.error_details)


class Transaction(object):
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

    def install(self, skip_recommends=False, force_configuration=None):
        """Run an apt-get transaction to install given packages.

        FreedomBox Service (Plinth) needs to be running as root when calling
        this. Currently, this is meant to be only during first time setup when
        --setup is argument is passed.

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

        """
        try:
            self._run_apt_command(['update'])
            extra_arguments = []
            if skip_recommends:
                extra_arguments.append('--skip-recommends')

            if force_configuration is not None:
                extra_arguments.append(
                    '--force-configuration={}'.format(force_configuration))

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
                _('installing'),
            'dlstatus':
                _('downloading'),
            'media-change':
                _('media change'),
            'pmconffile':
                _('configuration file: {file}').format(file=parts[1]),
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
