# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package holding all the privileged actions outside of apps."""

from .config import dropin_is_valid, dropin_link, dropin_unlink
from .packages import (filter_conffile_packages, install,
                       is_package_manager_busy, remove, update)
from .service import (disable, enable, is_enabled, is_running, mask, reload,
                      restart, start, stop, systemd_set_default,
                      try_reload_or_restart, try_restart, unmask)

__all__ = [
    'filter_conffile_packages', 'install', 'is_package_manager_busy', 'remove',
    'update', 'systemd_set_default', 'disable', 'enable', 'is_enabled',
    'is_running', 'mask', 'reload', 'restart', 'start', 'stop',
    'try_reload_or_restart', 'try_restart', 'unmask', 'dropin_is_valid',
    'dropin_link', 'dropin_unlink'
]
