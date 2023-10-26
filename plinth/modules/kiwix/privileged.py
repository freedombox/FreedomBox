# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Privileged actions for Kiwix content server.
"""

import os
import pathlib
import shutil
import subprocess
from xml.etree import ElementTree

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules import kiwix

# Only one central library is supported.
KIWIX_HOME = pathlib.Path('/var/lib/kiwix-server-freedombox')
LIBRARY_FILE = KIWIX_HOME / 'library_zim.xml'
CONTENT_DIR = KIWIX_HOME / 'content'


@privileged
def add_package(file_name: str):
    """Adds a content package to Kiwix.

    Adding packages is idempotent.

    Users can add content to Kiwix in multiple ways:
     - Upload a ZIM file
     - Provide a link to the ZIM file
     - Provide a magnet link to the ZIM file

    The commandline download manager aria2c is a dependency of kiwix-tools.
    aria2c is used for both HTTP and Magnet downloads.
    """
    kiwix.validate_file_name(file_name)

    # Moving files to the Kiwix library path ensures that
    # they can't be removed by other apps or users.
    zim_file_name = pathlib.Path(file_name).name
    CONTENT_DIR.mkdir(exist_ok=True)
    zim_file_dest = str(CONTENT_DIR / zim_file_name)
    shutil.chown(file_name, 'root', 'root')
    os.chmod(file_name, 0o644)
    shutil.move(file_name, zim_file_dest)

    _kiwix_manage_add(zim_file_dest)


def _kiwix_manage_add(zim_file: str):
    subprocess.check_call(['kiwix-manage', LIBRARY_FILE, 'add', zim_file])

    # kiwix-serve doesn't read the library file unless it is restarted.
    action_utils.service_try_restart('kiwix-server-freedombox')


@privileged
def uninstall() -> None:
    """Remove all content during uninstall."""
    shutil.rmtree(str(CONTENT_DIR), ignore_errors=True)
    LIBRARY_FILE.unlink(missing_ok=True)


@privileged
def list_packages() -> dict[str, dict[str, str]]:
    """Return the list of content packages configured in library file."""
    library = ElementTree.parse(LIBRARY_FILE).getroot()

    books = {}
    for book in library:
        path = book.attrib['path'].split('/')[-1]
        path = path.removesuffix('.zim').lower()  # Strip '.zim' from the path
        try:
            books[book.attrib['id']] = {
                'title': book.attrib['title'],
                'description': book.attrib['description'],
                'path': path
            }
        except KeyError:
            pass  # Ignore entries that don't have expected properties

    return books


@privileged
def delete_package(zim_id: str):
    """Remove a content package from the library file."""
    library = ElementTree.parse(LIBRARY_FILE).getroot()

    for book in library:
        try:
            if book.attrib['id'] != zim_id:
                continue

            subprocess.check_call(
                ['kiwix-manage', LIBRARY_FILE, 'remove', zim_id])
            (KIWIX_HOME / book.attrib['path']).unlink()
            action_utils.service_try_restart('kiwix-server-freedombox')
            return
        except KeyError:  # Expected properties not found on elements
            pass
