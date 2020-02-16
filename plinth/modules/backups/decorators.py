# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Decorators for the backup views.
"""

import functools
import os

from . import SESSION_PATH_VARIABLE


def delete_tmp_backup_file(function):
    """Decorator to delete uploaded backup files.

    XXX: Implement a better way to delete uploaded files.

    """
    @functools.wraps(function)
    def wrapper(request, *args, **kwargs):
        path = request.session.get(SESSION_PATH_VARIABLE, None)
        if path:
            if os.path.isfile(path):
                os.remove(path)
            del request.session[SESSION_PATH_VARIABLE]
        return function(request, *args, **kwargs)

    return wrapper
