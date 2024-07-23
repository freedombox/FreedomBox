# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Miniflux feed reader."""

import json
import os
import pathlib
import subprocess
from typing import Tuple
from urllib.parse import urlparse

import pexpect

from plinth import action_utils
from plinth.actions import privileged
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
    """Perform post-install actions for Miniflux."""
    vars_file = pathlib.Path(ENV_VARS_FILE)
    vars_file.parent.mkdir(parents=True, exist_ok=True)

    existing_settings = {}
    if is_non_empty_file(ENV_VARS_FILE):
        # Any comments in the file will be dropped.
        existing_settings = _env_file_to_dict(vars_file.read_text())

    new_settings = existing_settings | STATIC_SETTINGS
    vars_file.write_text(_dict_to_env_file(new_settings))


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
    raw_message = child.before.decode()
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
def create_admin_user(username: str, password: str):
    """Create a new admin user for Miniflux CLI.

    Raise exception if a user with the name already exists or otherwise fails.
    """
    _, json_message = _run_miniflux_interactively('--create-admin', username,
                                                  password)
    # user_id is allocated only when a new user is created successfully.
    if json_message and not json_message.get('user_id'):
        raise Exception(json_message.get('msg'))


@privileged
def reset_user_password(username: str, password: str):
    """Reset a user password using Miniflux CLI.

    Raise exception if the user does not exist or otherwise fails.
    """
    _run_miniflux_interactively('--reset-password', username, password)


@privileged
def uninstall():
    """Ensure that the database is removed."""
    action_utils.debconf_set_selections(
        ['miniflux miniflux/purge boolean true'])


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


# The following 3 methods are duplicated in tt-rss/privileged.py


def _run_as_postgres(command, stdin=None, stdout=None):
    """Run a command as postgres user."""
    command = ['sudo', '--user', 'postgres'] + command
    return subprocess.run(command, stdin=stdin, stdout=stdout, check=True)


@privileged
def dump_database():
    """Dump database to file."""
    config = _get_database_config()
    os.makedirs(os.path.dirname(DB_BACKUP_FILE), exist_ok=True)
    with open(DB_BACKUP_FILE, 'w', encoding='utf-8') as db_backup_file:
        process = _run_as_postgres(['pg_dumpall', '--roles-only'],
                                   stdout=subprocess.PIPE)
        db_backup_file.write(f'DROP ROLE IF EXISTS {config["user"]};\n')
        for line in process.stdout.decode().splitlines():
            if config['user'] in line:
                db_backup_file.write(line + '\n')

    with open(DB_BACKUP_FILE, 'a', encoding='utf-8') as db_backup_file:
        _run_as_postgres([
            'pg_dump', '--create', '--clean', '--if-exists', config['database']
        ], stdout=db_backup_file)


@privileged
def restore_database():
    """Restore database from file."""
    config = _get_database_config()

    # This is needed for old backups only. New backups include 'DROP DATABASE
    # IF EXISTS' and 'CREATE DATABASE' statements.
    _run_as_postgres(['dropdb', config['database']])
    _run_as_postgres(['createdb', config['database']])

    with open(DB_BACKUP_FILE, 'r', encoding='utf-8') as db_restore_file:
        _run_as_postgres(['psql', '--dbname', config['database']],
                         stdin=db_restore_file)
