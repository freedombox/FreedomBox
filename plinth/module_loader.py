# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Discover, load and manage FreedomBox applications.
"""

import collections
import importlib
import logging
import pathlib
import re
from typing import Optional

import django

from plinth import cfg
from plinth.signals import pre_module_loading

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
    for module_import_path in get_modules_to_load():
        module_name = module_import_path.split('.')[-1]
        try:
            loaded_modules[module_name] = importlib.import_module(
                module_import_path)
        except Exception as exception:
            logger.exception('Could not import %s: %s', module_import_path,
                             exception)
            if cfg.develop:
                raise


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
        module = _get_module_import_paths_from_file(file_)
        if module:
            modules.append(module)

    _modules_to_load = modules
    return modules


def get_module_import_path(module_name: str) -> str:
    """Return the import path for a module."""
    file_path = pathlib.Path(cfg.config_dir) / 'modules-enabled' / module_name
    return _get_module_import_paths_from_file(file_path)


def _get_module_import_paths_from_file(file_path: str) -> Optional[str]:
    """Read a module's import path from a file."""
    with file_path.open() as file_handle:
        for line in file_handle:
            line = re.sub('#.*', '', line)
            line = line.strip()
            if line:
                return line

    return None
