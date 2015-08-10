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

import django
import importlib
import logging
import os
import re

from plinth import cfg
from plinth import urls
from plinth.signals import pre_module_loading, post_module_loading

LOGGER = logging.getLogger(__name__)

loaded_modules = []
_modules_to_load = None


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    pre_module_loading.send_robust(sender="module_loader")
    modules = {}
    for module_name in get_modules_to_load():
        LOGGER.info('Importing %s', module_name)
        try:
            modules[module_name] = importlib.import_module(module_name)
        except Exception as exception:
            LOGGER.exception('Could not import %s: %s', module_name, exception)
            if cfg.debug:
                raise

        _include_module_urls(module_name)

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
            LOGGER.error('Unsatified dependency for module - %s',
                         module_name)

    LOGGER.debug('Module load order - %s', ordered_modules)

    for module_name in ordered_modules:
        _initialize_module(modules[module_name])
        loaded_modules.append(module_name)

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
            LOGGER.error('Not found or circular dependency - %s, %s',
                         module_name, dependency)
            raise

        _insert_modules(dependency, module, remaining_modules, ordered_modules)

    ordered_modules.append(module_name)


def _include_module_urls(module_name):
    """Include the module's URLs in global project URLs list"""
    namespace = module_name.split('.')[-1]
    url_module = module_name + '.urls'
    try:
        urls.urlpatterns += django.conf.urls.patterns(
            '', django.conf.urls.url(
                r'', django.conf.urls.include(url_module, namespace)))
    except ImportError:
        LOGGER.debug('No URLs for %s', module_name)
        if cfg.debug:
            raise


def _initialize_module(module):
    """Call initialization method in the module if it exists"""
    try:
        init = module.init
    except AttributeError:
        LOGGER.debug('No init() for module - %s', module.__name__)
        return

    try:
        init()
    except Exception as exception:
        LOGGER.exception('Exception while running init for %s: %s',
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
