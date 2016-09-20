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
Plinth module with utilites for performing application setup operations.
"""

import apt
import logging
import threading

from . import package
from .errors import PackageNotInstalledError
import plinth

logger = logging.getLogger(__name__)


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
        finally:
            self.is_finished = True
            self.current_operation = None

    def install(self, package_names):
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
        transaction.install()

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
        else:
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


def init(module_name, module):
    """Create a setup helper for a module for later use."""
    if not hasattr(module, 'setup_helper'):
        module.setup_helper = Helper(module_name, module)


def setup_modules(module_list=None, essential=False, allow_install=True):
    """Run setup on selected or essential modules."""
    logger.info('Running setup for modules, essential - %s, '
                'selected modules - %s', essential, module_list)
    for module_name, module in plinth.module_loader.loaded_modules.items():
        if essential and not getattr(module, 'is_essential', False):
            continue

        if module_list and module_name not in module_list:
            continue

        module.setup_helper.run(allow_install=allow_install)


def list_dependencies(module_list=None, essential=False):
    """Print list of packages required by selected or essential modules."""
    for module_name, module in plinth.module_loader.loaded_modules.items():
        if essential and not getattr(module, 'is_essential', False):
            continue

        if module_list and module_name not in module_list and \
           '*' not in module_list:
            continue

        for package_name in getattr(module, 'managed_packages', []):
            print(package_name)
