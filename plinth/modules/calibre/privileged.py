# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for calibre."""

import pathlib
import shutil

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules import calibre

LIBRARIES_PATH = pathlib.Path('/var/lib/calibre-server-freedombox/libraries')


@privileged
def list_libraries() -> list[str]:
    """Return the list of libraries setup."""
    libraries = []
    for library in LIBRARIES_PATH.glob('*/metadata.db'):
        libraries.append(str(library.parent.name))

    return libraries


@privileged
def create_library(name: str):
    """Create an empty library."""
    calibre.validate_library_name(name)
    library = LIBRARIES_PATH / name
    library.mkdir(mode=0o755)  # Raise exception if already exists
    action_utils.run(
        ['calibredb', '--with-library', library, 'list_categories'],
        check=False)

    # Force systemd StateDirectory= logic to assign proper ownership to the
    # DynamicUser=
    shutil.chown(LIBRARIES_PATH.parent, 'root', 'root')
    action_utils.service_try_restart(calibre.CalibreApp.DAEMON)


@privileged
def delete_library(name: str):
    """Delete a library and its contents."""
    calibre.validate_library_name(name)
    library = LIBRARIES_PATH / name
    shutil.rmtree(library)
    action_utils.service_try_restart(calibre.CalibreApp.DAEMON)


@privileged
def uninstall():
    """Remove all libraries during uninstall."""
    shutil.rmtree(LIBRARIES_PATH)
