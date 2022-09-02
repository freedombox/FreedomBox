# SPDX-License-Identifier: AGPL-3.0-or-later
"""Manage email aliases stored in sqlite database."""

import contextlib
import pwd
import sqlite3
from dataclasses import dataclass

from . import privileged


@dataclass
class Alias:
    value: str
    name: str


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


def get(username):
    """Get all aliases of a user."""
    query = 'SELECT name, value FROM alias WHERE value=?'
    with _get_cursor() as cursor:
        rows = cursor.execute(query, (username, ))
        return [Alias(**row) for row in rows]


def exists(name):
    """Return whether alias is already taken."""
    try:
        pwd.getpwnam(name)
        return True
    except KeyError:
        pass

    with _get_cursor() as cursor:
        query = 'SELECT COUNT(*) FROM alias WHERE name=?'
        cursor.execute(query, (name, ))
        return cursor.fetchone()[0] != 0


def put(username, name):
    """Insert if not exists a new alias."""
    query = 'INSERT INTO alias (name, value) VALUES (?, ?)'
    with _get_cursor() as cursor:
        try:
            cursor.execute(query, (name, username))
        except sqlite3.IntegrityError:
            pass  # Alias exists, rare since we are already checking


def delete(username, aliases):
    """Delete a set of aliases."""
    query = 'DELETE FROM alias WHERE value=? AND name=?'
    parameter_seq = ((username, name) for name in aliases)
    with _get_cursor() as cursor:
        cursor.execute('BEGIN')
        cursor.executemany(query, parameter_seq)
        cursor.execute('COMMIT')


def first_setup():
    """Create the database file and schema inside it."""
    privileged.aliases.setup_aliases()

    # Create schema if not exists
    query = '''
BEGIN;
CREATE TABLE IF NOT EXISTS alias (
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (name)
);
COMMIT;
'''
    with _get_cursor() as cursor:
        cursor.executescript(query)


def setup_common_aliases(username):
    """Create aliases for common mailboxes described in RFC2142.

    See: https://datatracker.ietf.org/doc/html/rfc2142
    """
    aliases = [
        'mailer-daemon', 'postmaster', 'nobody', 'webmaster', 'www',
        'hostmaster', 'info', 'support', 'abuse', 'noc', 'security'
        'usenet', 'news', 'ftp'
    ]
    for alias in aliases:
        if not exists(alias):
            put(username, alias)
