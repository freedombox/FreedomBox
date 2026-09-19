# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Decorators for the backup views.
"""

import functools

from . import privileged, SESSION_PATH_VARIABLE


def delete_tmp_backup_file(function):
    """Decorator to delete uploaded backup files.

    XXX: Implement a better way to delete uploaded files.

    """

    @functools.wraps(function)
    def wrapper(request, *args, **kwargs):
        path = request.session.get(SESSION_PATH_VARIABLE, None)
        if path:
            privileged.remove_uploaded_archive(path)
            del request.session[SESSION_PATH_VARIABLE]
        return function(request, *args, **kwargs)

    return wrapper
