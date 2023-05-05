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


def _get_modules_enabled_paths():
    """Return list of paths from which enabled modules list must be read."""
    return [
        pathlib.Path('/usr/share/freedombox/modules-enabled/'),
        pathlib.Path('/etc/plinth/modules-enabled/'),  # For compatibility
        pathlib.Path('/etc/freedombox/modules-enabled/'),
    ]


def _get_modules_enabled_files_to_read():
    """Return the list of files containing modules import paths."""
    module_files = {}
    for path in _get_modules_enabled_paths():
        directory = pathlib.Path(path)
        files = list(directory.glob('*'))
        for file_ in files:
            # Omit hidden or backup files
            if file_.name.startswith('.') or '.dpkg' in file_.name:
                continue

            if file_.is_symlink() and str(file_.resolve()) == '/dev/null':
                module_files.pop(file_.name, None)
                continue

            module_files[file_.name] = file_

    if module_files:
        return module_files.values()

    # './setup.py install' has not been executed yet. Pickup files to load
    # from local module directories.
    directory = pathlib.Path(__file__).parent
    glob_pattern = 'modules/*/data/usr/share/freedombox/modules-enabled/*'
    return list(directory.glob(glob_pattern))


def get_modules_to_load():
    """Get the list of modules to be loaded"""
    global _modules_to_load
    if _modules_to_load is not None:
        return _modules_to_load

    modules = []
    for file_ in _get_modules_enabled_files_to_read():
        module = _read_module_import_paths_from_file(file_)
        if module:
            modules.append(module)

    _modules_to_load = modules
    return modules


def get_module_import_path(module_name: str) -> str:
    """Return the import path for a module."""
    import_path_file = None
    for path in _get_modules_enabled_paths():
        file_ = path / module_name
        if file_.exists():
            import_path_file = file_

        if file_.is_symlink() and str(file_.resolve()) == '/dev/null':
            import_path_file = None

    if not import_path_file:
        # './setup.py install' has not been executed yet. Pickup files to load
        # from local module directories.
        directory = pathlib.Path(__file__).parent
        import_path_file = (directory /
                            f'modules/{module_name}/data/usr/share/'
                            f'freedombox/modules-enabled/{module_name}')

    if not import_path_file:
        raise ValueError('Unknown module')

    import_path = _read_module_import_paths_from_file(import_path_file)
    if not import_path:
        raise ValueError('Module disabled')

    return import_path


def _read_module_import_paths_from_file(
        file_path: pathlib.Path) -> Optional[str]:
    """Read a module's import path from a file."""
    with file_path.open() as file_handle:
        for line in file_handle:
            line = re.sub('#.*', '', line)
            line = line.strip()
            if line:
                return line

    return None
