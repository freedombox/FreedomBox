"""Manages email aliases"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib
import pwd
import sqlite3

from plinth import actions

from . import models


@contextlib.contextmanager
def _get_cursor():
    """Return a DB cursor as context manager."""
    # Turn ON autocommit mode
    db_path = '/var/lib/postfix/freedombox-aliases/aliases.sqlite3'
    connection = sqlite3.connect(db_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        yield cursor
    finally:
        connection.close()


def get(uid_number):
    """Get all aliases of a user."""
    query = 'SELECT * FROM Alias WHERE uid_number=?'
    with _get_cursor() as cursor:
        rows = cursor.execute(query, (uid_number, ))
        result = [models.Alias(**row) for row in rows]
        return result


def exists(email_name):
    """Return whether alias is already taken."""
    try:
        pwd.getpwnam(email_name)
        return True
    except KeyError:
        pass

    with _get_cursor() as cursor:
        query = 'SELECT COUNT(*) FROM Alias WHERE email_name=?'
        cursor.execute(query, (email_name, ))
        return cursor.fetchone()[0] != 0


def put(uid_number, email_name):
    """Insert if not exists a new alias."""
    query = '''
INSERT INTO Alias(email_name, uid_number, status)
    SELECT ?,?,? WHERE NOT EXISTS (
        SELECT 1 FROM Alias WHERE email_name=?
    )
'''
    with _get_cursor() as cursor:
        cursor.execute(query, (email_name, uid_number, 1, email_name))


def delete(uid_number, alias_list):
    """Delete a set of aliases."""
    query = 'DELETE FROM Alias WHERE uid_number=? AND email_name=?'
    parameter_seq = ((uid_number, alias) for alias in alias_list)
    with _get_cursor() as cursor:
        cursor.execute('BEGIN')
        cursor.executemany(query, parameter_seq)
        cursor.execute('COMMIT')


def enable(uid_number, alias_list):
    """Enable a list of aliases."""
    return _set_status(uid_number, alias_list, 1)


def disable(uid_number, alias_list):
    """Disable a list of aliases."""
    return _set_status(uid_number, alias_list, 0)


def _set_status(uid_number, alias_list, status):
    """Set the status value of a list of aliases."""
    query = 'UPDATE Alias SET status=? WHERE uid_number=? AND email_name=?'
    parameter_seq = ((status, uid_number, alias) for alias in alias_list)
    with _get_cursor() as cursor:
        cursor.execute('BEGIN')
        cursor.executemany(query, parameter_seq)
        cursor.execute('COMMIT')


def first_setup():
    """Create the database file and schema inside it."""
    actions.superuser_run('email_server', ['-i', 'aliases', 'setup'])

    # Create schema if not exists
    query = '''
PRAGMA journal_mode=WAL;
BEGIN;
CREATE TABLE IF NOT EXISTS Alias (
    email_name TEXT NOT NULL,
    uid_number INTEGER NOT NULL,
    status INTEGER NOT NULL,
    PRIMARY KEY (email_name)
);
COMMIT;
'''
    with _get_cursor() as cursor:
        cursor.executescript(query)
