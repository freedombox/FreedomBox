# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure sharing."""

import pathlib

from plinth.actions import privileged

APACHE_CONFIGURATION = '/etc/apache2/conf-available/sharing-freedombox.conf'


@privileged
def setup():
    """Create an empty apache configuration file."""
    path = pathlib.Path(APACHE_CONFIGURATION)
    if not path.exists():
        path.touch()
