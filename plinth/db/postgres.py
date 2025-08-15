# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities to help with PostgreSQL databases.

Uses utilities from 'postgres' package such as 'psql' and 'pg_dump'.
"""

import os
import pathlib

from plinth import action_utils


def _run_as(command, **kwargs):
    """Run a command as 'postgres' user."""
    command = ['sudo', '--user', 'postgres'] + command
    return action_utils.run(command, check=True, **kwargs)


def run_query(query):
    """Run a database query as 'postgres' user.

    Does not ensure that database server is running.
    """
    env = os.environ.copy()
    env['ON_ERROR_EXIT'] = '1'
    return _run_as(['psql', '--echo-errors'], env=env,
                   input=query.encode('utf-8'))


def _create_user(database_user: str, database_password: str):
    """Create a new user account with given credentials.

    Ignore errors if user already exists. Set password on the account either
    way. Passwords must be alphanumeric.
    """
    query = f'''
DO $$
BEGIN
    CREATE ROLE {database_user} WITH
        PASSWORD '{database_password}'
        NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN NOREPLICATION
        NOBYPASSRLS;
EXCEPTION WHEN duplicate_object THEN
    ALTER ROLE {database_user} WITH
        PASSWORD '{database_password}';
END
$$;'''
    run_query(query)


def _drop_user(database_user: str):
    """Remove a user account with given username."""
    run_query(f'DROP ROLE {database_user};')


def create_database(database_name: str, database_user: str,
                    database_password: str):
    """Create a new database and a user account to access it.

    Database server is temporarily started if it is not running.
    """
    query = f'''
CREATE EXTENSION IF NOT EXISTS dblink;
DO $$
BEGIN
    PERFORM dblink_exec('',
        'CREATE DATABASE {database_name} WITH OWNER {database_user}');
EXCEPTION WHEN duplicate_database THEN
    ALTER DATABASE {database_name}
        OWNER TO {database_user};
END
$$;'''
    with action_utils.service_ensure_running('postgresql'):
        _create_user(database_user, database_password)
        run_query(query)


def drop_database(database_name: str, database_user: str):
    """Delete the database and the user account owning it.

    Database server is temporarily started if it is not running.
    """
    query = f'DROP DATABASE {database_name};'
    with action_utils.service_ensure_running('postgresql'):
        run_query(query)
        _drop_user(database_user)


def dump_database(backup_file: str | pathlib.Path, database_name: str):
    """Dump PostgreSQL database to a file.

    Database server is temporarily started if it is not running. Overwrite
    file if it exists.
    """
    backup_path = pathlib.Path(backup_file)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with action_utils.service_ensure_running('postgresql'):
        with open(backup_path, 'w', encoding='utf-8') as file_handle:
            _run_as([
                'pg_dump', '--create', '--clean', '--if-exists', database_name
            ], stdout=file_handle)


def restore_database(backup_file: str | pathlib.Path, database_name: str,
                     database_user: str, database_password: str):
    """Restore database from a file.

    Database server is temporarily started if it is not running. User account
    is removed and recreated if it already exists. Drop database and recreate
    if it already exists.
    """
    with action_utils.service_ensure_running('postgresql'):
        drop_database(database_name, database_user)
        create_database(database_name, database_user, database_password)
        with open(backup_file, 'r', encoding='utf-8') as file_handle:
            _run_as(['psql', '--dbname', database_name], stdin=file_handle)
