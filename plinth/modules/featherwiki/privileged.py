# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Feather Wiki."""

import pathlib
import re
import shutil
import tempfile
import urllib.request

from plinth.actions import privileged

# Needs to be changed on a new release
EMPTY_WIKI_FILE = 'https://feather.wiki/builds/v1.8.x/FeatherWiki_Skylark.html'

wiki_dir = pathlib.Path('/var/lib/featherwiki')


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
    """Initialize wiki with the latest version of Feather Wiki."""
    file_name = _normalize_wiki_file_name(file_name)
    response = urllib.request.urlopen(EMPTY_WIKI_FILE)
    file_path = wiki_dir / file_name
    if file_path.exists():
        raise ValueError('Wiki exists')

    file_path.write_bytes(response.read())
    _set_ownership(file_path)


@privileged
def add_wiki_file(upload_file: str):
    """Add an uploaded wiki file."""
    upload_file_path = pathlib.Path(upload_file)
    temp_dir = tempfile.gettempdir()
    if not upload_file_path.is_relative_to(temp_dir):
        raise Exception('Uploaded file is not in expected temp directory.')

    file_name = _normalize_wiki_file_name(upload_file_path.name)
    file_path = wiki_dir / file_name
    if file_path.exists():
        raise ValueError('Wiki exists')

    shutil.move(upload_file_path, file_path)
    _set_ownership(file_path)


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
