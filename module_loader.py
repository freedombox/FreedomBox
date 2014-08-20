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

import urls
import cfg

LOGGER = logging.getLogger(__name__)

LOADED_MODULES = []


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    module_names = []
    modules = {}
    for name in os.listdir('modules/enabled'):
        full_name = 'modules.{module}'.format(module=name)

        LOGGER.info('Importing %s', full_name)
        try:
            module = importlib.import_module(full_name)
            modules[name] = module
            module_names.append(name)
        except Exception as exception:
            LOGGER.exception('Could not import modules/%s: %s',
                             name, exception)
            if cfg.debug:
                raise

        _include_module_urls(full_name, name)

    ordered_modules = []
    remaining_modules = dict(modules)
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
        LOADED_MODULES.append(module_name)


def _insert_modules(module_name, module, remaining_modules, ordered_modules):
    """Insert modules into a list based on dependency order"""
    if module_name in ordered_modules:
        return

    dependencies = []
    try:
        dependencies = module.DEPENDS
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


def _include_module_urls(module_name, namespace):
    """Include the module's URLs in global project URLs list"""
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


def get_template_directories():
    """Return the list of template directories"""
    directory = os.path.dirname(os.path.abspath(__file__))
    core_directory = os.path.join(directory, 'templates')

    directories = set((core_directory,))
    for name in os.listdir('modules/enabled'):
        directories.add(os.path.join(directory, 'modules', name, 'templates'))

    return directories
