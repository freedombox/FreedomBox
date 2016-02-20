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

import logging
import threading

from . import package
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

    def run(self):
        """Execute the setup process."""
        # Setup for the module is already running
        if self.current_operation:
            return

        current_version = self.get_setup_version()
        if current_version >= self.module.version:
            return

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
        logger.info('Running install for module - %s, packages - %s',
                    self.module_name, package_names)
        transaction = package.Transaction(package_names)
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


def setup_all_modules(essential=False):
    """Run setup on all essential modules and exit."""
    logger.info('Running setup for all modules, essential - %s', essential)
    for module_name, module in plinth.module_loader.loaded_modules.items():
        if essential and not getattr(module, 'is_essential', False):
            continue

        module.setup_helper.run()
