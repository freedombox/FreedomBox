# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure TiddlyWiki."""

import pathlib
import re
import shutil
import urllib.request

from plinth import action_utils
from plinth.actions import privileged

EMPTY_WIKI_FILE = 'https://ftp.freedombox.org/pub/tiddlywiki/empty.html'

wiki_dir = pathlib.Path('/var/lib/tiddlywiki')


def _set_ownership(path: pathlib.Path):
    """Makes www-data:www-data the owner of the give path."""
    shutil.chown(path, user='www-data', group='www-data')


@privileged
def setup():
    """Setup wiki dir and CGI script."""
    wiki_dir.mkdir(parents=True, exist_ok=True)
    _set_ownership(wiki_dir)


def _normalize_wiki_file_name(name):
    """Return a normalized file name from a wiki name."""
    file_name = name.replace(' ', '_')
    invalid_characters = r'[\/\\\:\*\?\"\'\<\>\|]'
    file_name = re.sub(invalid_characters, '', file_name)
    if not file_name.endswith('.html'):
        return file_name + '.html'

    return file_name


@privileged
def create_wiki(file_name: str):
    """Initialize wiki with the latest version of TiddlyWiki."""
    file_name = _normalize_wiki_file_name(file_name)
    response = urllib.request.urlopen(EMPTY_WIKI_FILE)
    file_path = wiki_dir / file_name
    if file_path.exists():
        raise ValueError('Wiki exists')

    file_path.write_bytes(response.read())
    _set_ownership(file_path)


@privileged
def add_wiki_file(file_name: str, temporary_file_path: str):
    """Add an uploaded wiki file."""
    action_utils.move_uploaded_file(temporary_file_path, wiki_dir, file_name,
                                    allow_overwrite=False, user='www-data',
                                    group='www-data', permissions=0o644)


@privileged
def rename_wiki(old_name: str, new_name: str):
    """Rename wiki file."""
    old_name = _normalize_wiki_file_name(old_name)
    new_name = _normalize_wiki_file_name(new_name)
    file_path = wiki_dir / new_name
    if file_path.exists():
        raise ValueError('Wiki exists')

    (wiki_dir / old_name).rename(file_path)


@privileged
def delete_wiki(file_name: str):
    """Delete one wiki file by name."""
    file_name = _normalize_wiki_file_name(file_name)
    (wiki_dir / file_name).unlink(missing_ok=True)


@privileged
def uninstall():
    """Delete all the wiki content."""
    shutil.rmtree(wiki_dir)
