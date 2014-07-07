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
import os

import cfg
import urls


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    module_names = []
    modules = {}
    for name in os.listdir('modules/enabled'):
        full_name = 'modules.{module}'.format(module=name)

        cfg.log.info('Importing {full_name}'.format(full_name=full_name))
        try:
            module = importlib.import_module(full_name)
            modules[name] = module
            module_names.append(name)
        except ImportError as exception:
            cfg.log.error(
                'Could not import modules/{module}: {exception}'
                .format(module=name, exception=exception))

        _include_module_urls(full_name)

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
            cfg.log.error('Unsatified dependency for module - %s' %
                          (module_name,))

    cfg.log.debug('Module load order - %s' % ordered_modules)

    for module_name in ordered_modules:
        _initialize_module(modules[module_name])


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
            cfg.log.error('Not found or circular dependency - %s, %s' %
                          (module_name, dependency))
            raise

        _insert_modules(dependency, module, remaining_modules, ordered_modules)

    ordered_modules.append(module_name)


def _include_module_urls(module_name):
    """Include the module's URLs in global project URLs list"""
    url_module = module_name + '.urls'
    try:
        urls.urlpatterns += django.conf.urls.patterns(
            '', django.conf.urls.url(
                r'', django.conf.urls.include(url_module)))
    except ImportError:
        cfg.log.debug('No URLs for {module}'.format(module=module_name))


def _initialize_module(module):
    """Call initialization method in the module if it exists"""
    try:
        init = module.init
    except AttributeError:
        cfg.log.debug('No init() for module - {module}'
                      .format(module=module.__name__))
        return

    try:
        init()
    except Exception as exception:
        cfg.log.error('Exception while running init for {module}: {exception}'
                      .format(module=module, exception=exception))


def get_template_directories():
    """Return the list of template directories"""
    directory = os.path.dirname(os.path.abspath(__file__))
    core_directory = os.path.join(directory, 'templates')

    directories = set((core_directory,))
    for name in os.listdir('modules/enabled'):
        directories.add(os.path.join('modules', name, 'templates'))

    cfg.log.info('Template directories - %s' % directories)

    return directories
