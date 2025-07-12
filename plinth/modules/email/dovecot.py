# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities to configure Dovecot."""

import apt

from plinth.utils import Version


def is_version_24():
    """Return the currently installed version of Dovecot."""
    cache = apt.Cache()
    try:
        version = cache['dovecot-core'].installed.version
    except KeyError:
        return True

    return Version(version) >= Version('1:2.4')
