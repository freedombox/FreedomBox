# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Discover, load and manage FreedomBox applications.
"""

import collections
import importlib
import inspect
import logging
import pathlib
import re

import django

from plinth import app, cfg, setup
from plinth.signals import post_module_loading, pre_module_loading

logger = logging.getLogger(__name__)

loaded_modules = collections.OrderedDict()
_modules_to_load = None


def include_urls():
    """Include the URLs of the modules into main Django project."""
    for module_import_path in get_modules_to_load():
        module_name = module_import_path.split('.')[-1]
        _include_module_urls(module_import_path, module_name)


def _is_module_essential(module):
    """Return if a module is an essential module."""
    return getattr(module, 'is_essential', False)


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    pre_module_loading.send_robust(sender="module_loader")
    modules = {}
    for module_import_path in get_modules_to_load():
        module_name = module_import_path.split('.')[-1]
        try:
            modules[module_name] = importlib.import_module(module_import_path)
        except Exception as exception:
            logger.exception('Could not import %s: %s', module_import_path,
                             exception)
            if cfg.develop:
                raise

    ordered_modules = []
    remaining_modules = dict(modules)  # Make a copy
    # Place all essential modules ahead of others in module load order
    sorted_modules = sorted(
        modules, key=lambda module: not _is_module_essential(modules[module]))
    for module_name in sorted_modules:
        if module_name not in remaining_modules:
            continue

        module = remaining_modules.pop(module_name)
        try:
            _insert_modules(module_name, module, remaining_modules,
                            ordered_modules)
        except KeyError:
            logger.error('Unsatified dependency for module - %s', module_name)

    for module_name in ordered_modules:
        loaded_modules[module_name] = modules[module_name]


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
    from plinth import urls
    url_module = module_import_path + '.urls'
    try:
        urls.urlpatterns += [
            django.urls.re_path(r'',
                                django.urls.include((url_module, module_name)))
        ]
    except ImportError:
        logger.debug('No URLs for %s', module_name)
        if cfg.develop:
            raise


def apps_init():
    """Create apps by constructing them with components."""
    logger.info('Initializing apps - %s', ', '.join(loaded_modules))
    for module_name, module in loaded_modules.items():
        _initialize_module(module_name, module)


def _initialize_module(module_name, module):
    """Perform module initialization"""

    # Perform setup related initialization on the module
    setup.init(module_name, module)

    try:
        module_classes = inspect.getmembers(module, inspect.isclass)
        app_class = [
            cls for cls in module_classes if issubclass(cls[1], app.App)
        ]
        if module_classes and app_class:
            module.app = app_class[0][1]()
    except Exception as exception:
        logger.exception('Exception while running init for %s: %s', module,
                         exception)
        if cfg.develop:
            raise


def apps_post_init():
    """Run post initialization on each app."""
    for module in loaded_modules.values():
        if not hasattr(module, 'app') or not module.app:
            continue

        try:
            module.app.post_init()
            if not module.app.needs_setup() and module.app.is_enabled():
                module.app.set_enabled(True)
        except Exception as exception:
            logger.exception('Exception while running post init for %s: %s',
                             module, exception)
            if cfg.develop:
                raise

    logger.debug('App initialization completed.')
    post_module_loading.send_robust(sender="module_loader")


def get_modules_to_load():
    """Get the list of modules to be loaded"""
    global _modules_to_load
    if _modules_to_load is not None:
        return _modules_to_load

    directory = pathlib.Path(cfg.config_dir) / 'modules-enabled'
    files = list(directory.glob('*'))
    if not files:
        # './setup.py install' has not been executed yet. Pickup files to load
        # from local module directories.
        directory = pathlib.Path(__file__).parent
        files = list(
            directory.glob('modules/*/data/etc/plinth/modules-enabled/*'))

    # Omit hidden files
    files = [
        file_ for file_ in files
        if not file_.name.startswith('.') and '.dpkg' not in file_.name
    ]

    modules = []
    for file_ in files:
        with file_.open() as file_handle:
            for line in file_handle:
                line = re.sub('#.*', '', line)
                line = line.strip()
                if line:
                    modules.append(line)

    _modules_to_load = modules
    return modules
