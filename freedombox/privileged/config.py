# SPDX-License-Identifier: AGPL-3.0-or-later
"""Symlink and unlink configuration files into /etc."""

import importlib
import inspect
import shutil

from plinth import app as app_module
from plinth import module_loader
from plinth.actions import privileged


def _get_managed_dropin_config(app_id: str, path: str):
    """Check that this is a path managed by the specified app."""
    module_path = module_loader.get_module_import_path(app_id)
    module = importlib.import_module(module_path)
    module_classes = inspect.getmembers(module, inspect.isclass)
    app_classes = [
        cls[1] for cls in module_classes if issubclass(cls[1], app_module.App)
    ]

    for cls in app_classes:
        app = cls()
        from plinth.config import DropinConfigs
        components = app.get_components_of_type(DropinConfigs)
        for component in components:
            if path in component.etc_paths:
                return component

    raise AssertionError('Not a managed drop-in config')


@privileged
def dropin_is_valid(app_id: str, path: str, copy_only: bool,
                    unlink_invalid: bool = False) -> bool:
    """Check if symlink from /etc/ to /usr/share/freedombox/etc is valid.

    Optionally, drop the link if it is invalid.
    """
    component = _get_managed_dropin_config(app_id, path)
    etc_path = component.get_etc_path(path)
    target = component.get_target_path(path)
    if etc_path.exists() or etc_path.is_symlink():
        if (not copy_only and etc_path.is_symlink()
                and etc_path.readlink() == target):
            return True

        if (copy_only and etc_path.is_file()
                and etc_path.read_text() == target.read_text()):
            return True

        if unlink_invalid:
            etc_path.unlink(missing_ok=True)

    return False


@privileged
def dropin_link(app_id: str, path: str, copy_only: bool):
    """Create a symlink from /etc/ to /usr/share/freedombox/etc."""
    component = _get_managed_dropin_config(app_id, path)
    target = component.get_target_path(path)
    etc_path = component.get_etc_path(path)
    etc_path.parent.mkdir(parents=True, exist_ok=True)
    if copy_only:
        shutil.copyfile(target, etc_path)
    else:
        etc_path.symlink_to(target)


@privileged
def dropin_unlink(app_id: str, path: str, missing_ok: bool = False):
    """Remove a symlink in /etc/."""
    component = _get_managed_dropin_config(app_id, path)
    etc_path = component.get_etc_path(path)
    etc_path.unlink(missing_ok=missing_ok)
