# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Compare Debian package version numbers.
"""

from functools import total_ordering

from apt import apt_pkg


@total_ordering
class Version:
    """The version number of a Debian package."""

    def __init__(self, version: str):
        self.version = version

    def __eq__(self, other):
        return apt_pkg.version_compare(self.version, other.version) == 0

    def __lt__(self, other):
        return apt_pkg.version_compare(self.version, other.version) < 0
