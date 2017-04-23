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
Discover, load and manage Plinth modules
"""

import collections
import django
import importlib
import logging
import os
import re

from plinth import cfg
from plinth import urls
from plinth import setup
from plinth.signals import pre_module_loading, post_module_loading

logger = logging.getLogger(__name__)

loaded_modules = collections.OrderedDict()
_modules_to_load = None


def include_urls():
    """Include the URLs of the modules into main Django project."""
    for module_import_path in get_modules_to_load():
        module_name = module_import_path.split('.')[-1]
        _include_module_urls(module_import_path, module_name)


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    pre_module_loading.send_robust(sender="module_loader")
    modules = {}
    for module_import_path in get_modules_to_load():
        logger.debug('Importing %s', module_import_path)
        module_name = module_import_path.split('.')[-1]
        try:
            modules[module_name] = importlib.import_module(module_import_path)
        except Exception as exception:
            logger.exception('Could not import %s: %s', module_import_path,
                             exception)
            if cfg.debug:
                raise

    ordered_modules = []
    remaining_modules = dict(modules)  # Make a copy
    for module_name in modules:
        if module_name not in remaining_modules:
            continue

        module = remaining_modules.pop(module_name)
        try:
            _insert_modules(module_name, module, remaining_modules,
                            ordered_modules)
        except KeyError:
            logger.error('Unsatified dependency for module - %s',
                         module_name)

    logger.info('Module load order - %s', ordered_modules)

    for module_name in ordered_modules:
        _initialize_module(module_name, modules[module_name])
        loaded_modules[module_name] = modules[module_name]

    post_module_loading.send_robust(sender="module_loader")


def _insert_modules(module_name, module, remaining_modules, ordered_modules):
    """Insert modules into a list based on dependency order"""
    if module_name in ordered_modules:
        return

    dependencies = []
    try:
        dependencies = module.depends
    except AttributeError:
        pass

    for dependency in dependencies:
        if dependency in ordered_modules:
            continue

        try:
            module = remaining_modules.pop(dependency)
        except KeyError:
            logger.error('Not found or circular dependency - %s, %s',
                         module_name, dependency)
            raise

        _insert_modules(dependency, module, remaining_modules, ordered_modules)

    ordered_modules.append(module_name)


def _include_module_urls(module_import_path, module_name):
    """Include the module's URLs in global project URLs list"""
    url_module = module_import_path + '.urls'
    try:
        urls.urlpatterns += [
            django.conf.urls.url(
                r'', django.conf.urls.include(url_module, module_name))]
    except ImportError:
        logger.debug('No URLs for %s', module_name)
        if cfg.debug:
            raise


def _initialize_module(module_name, module):
    """Call initialization method in the module if it exists"""
    # Perform setup related initialization on the module
    setup.init(module_name, module)

    try:
        init = module.init
    except AttributeError:
        logger.debug('No init() for module - %s', module.__name__)
        return

    try:
        init()
    except Exception as exception:
        logger.exception('Exception while running init for %s: %s',
                         module, exception)
        if cfg.debug:
            raise


def get_modules_to_load():
    """Get the list of modules to be loaded"""
    global _modules_to_load
    if _modules_to_load is not None:
        return _modules_to_load

    modules = []
    module_directory = os.path.join(cfg.config_dir, 'modules-enabled')

    # Omit hidden files
    file_names = [file_name
                  for file_name in os.listdir(module_directory)
                  if not file_name.startswith('.') and '.dpkg' not in file_name]

    for file_name in file_names:
        full_file_name = os.path.join(module_directory, file_name)
        with open(full_file_name, 'r') as file_handle:
            for line in file_handle:
                line = re.sub('#.*', '', line)
                line = line.strip()
                if line:
                    modules.append(line)

    _modules_to_load = modules
    return modules
