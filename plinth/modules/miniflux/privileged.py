# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Miniflux feed reader."""

import json
import os
import pathlib
import shutil
from typing import Tuple
from urllib.parse import urlparse

import pexpect

from plinth import action_utils
from plinth.actions import privileged, secret_str
from plinth.db import postgres
from plinth.utils import is_non_empty_file

STATIC_SETTINGS = {
    'BASE_URL': 'http://localhost/miniflux/',
    'RUN_MIGRATIONS': 1,
    'PORT': 8788
}

ENV_VARS_FILE = '/etc/miniflux/freedombox.conf'
DATABASE_FILE = '/etc/miniflux/database'
DB_BACKUP_FILE = '/var/lib/plinth/backups-data/miniflux-database.sql'


def _dict_to_env_file(dictionary: dict[str, str]) -> str:
    """Write a dictionary into a systemd environment file format."""
    return "\n".join((f"{k}={v}" for k, v in dictionary.items()))


def _env_file_to_dict(env_vars: str) -> dict[str, str]:
    """Return systemd environtment variables as a dictionary."""
    return {
        line.split('=')[0]: line.split('=')[1].strip()
        for line in env_vars.splitlines()
        if line.strip() and not line.strip().startswith('#')
    }


@privileged
def pre_setup():
    """Perform pre-install actions for Miniflux."""
    vars_file = pathlib.Path(ENV_VARS_FILE)
    vars_file.parent.mkdir(parents=True, exist_ok=True)

    existing_settings = {}
    if is_non_empty_file(ENV_VARS_FILE):
        # Any comments in the file will be dropped.
        existing_settings = _env_file_to_dict(vars_file.read_text())

    new_settings = existing_settings | STATIC_SETTINGS
    vars_file.write_text(_dict_to_env_file(new_settings))


@privileged
def setup(old_version: int):
    """Perform post-install actions for Miniflux."""
    # Fix incorrect permissions on database file in version 2.2.0-2. See
    # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1081562 . Can be
    # removed after the fix for the bug reaches Trixie/testing.
    shutil.chown(DATABASE_FILE, user='miniflux', group='root')
    if not old_version or action_utils.service_is_enabled('miniflux'):
        # If the service was tried too many times already, it won't
        # successfully restart.
        action_utils.service_reset_failed('miniflux')
        action_utils.service_restart('miniflux')


def _run_miniflux_interactively(command: str, username: str,
                                password: str) -> Tuple[str, dict]:
    """Fill interactive terminal prompt for username and password."""
    args = ['-c', '/etc/miniflux/miniflux.conf', command]
    os.environ['LOG_FORMAT'] = 'json'
    child = pexpect.spawn('miniflux', args, env=os.environ)

    # The CLI is in English only.
    child.expect('Enter Username: ')
    child.sendline(username)

    child.expect('Enter Password: ')
    child.sendline(password)

    child.expect(pexpect.EOF)
    raw_message = child.before.decode()  # type: ignore
    try:
        json_message = json.loads(raw_message)
    except (KeyError, json.JSONDecodeError):
        json_message = {}

    child.close()
    if child.exitstatus or child.signalstatus:
        message = json_message.get('msg') if json_message else raw_message
        raise Exception(message)

    return raw_message, json_message


@privileged
def create_admin_user(username: str, password: secret_str):
    """Create a new admin user for Miniflux CLI.

    Raise exception if a user with the name already exists or otherwise fails.
    """
    _, json_message = _run_miniflux_interactively('--create-admin', username,
                                                  password)
    # user_id is allocated only when a new user is created successfully.
    if json_message and not json_message.get('user_id'):
        raise Exception(json_message.get('msg'))


@privileged
def reset_user_password(username: str, password: secret_str):
    """Reset a user password using Miniflux CLI.

    Raise exception if the user does not exist or otherwise fails.
    """
    _run_miniflux_interactively('--reset-password', username, password)


@privileged
def uninstall():
    """Ensure that the database is removed."""
    action_utils.debconf_set_selections([
        'miniflux miniflux/purge boolean true',
        'miniflux miniflux/dbconfig-install boolean true',
        'miniflux miniflux/dbconfig-reinstall boolean true'
        'miniflux miniflux/dbconfig-upgrade boolean true',
        'miniflux miniflux/dbconfig-remove boolean true',
    ])


def _get_database_config():
    """Retrieve database credentials."""
    db_connection_string = pathlib.Path(DATABASE_FILE).read_text().strip()
    parsed_url = urlparse(db_connection_string)
    return {
        'user': parsed_url.username,
        'password': parsed_url.password,
        'database': parsed_url.path.lstrip('/'),
        'host': parsed_url.hostname,
    }


@privileged
def dump_database():
    """Dump database to file."""
    config = _get_database_config()
    postgres.dump_database(DB_BACKUP_FILE, config['database'])


@privileged
def restore_database():
    """Restore database from file."""
    config = _get_database_config()
    postgres.restore_database(DB_BACKUP_FILE, config['database'],
                              config['user'], config['password'])
