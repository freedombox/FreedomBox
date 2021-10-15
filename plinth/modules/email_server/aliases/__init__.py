"""Manages email aliases"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib
import pwd
import sqlite3

from plinth import actions

from . import models

map_db_schema_script = """
PRAGMA journal_mode=WAL;
BEGIN;
CREATE TABLE IF NOT EXISTS Alias (
    email_name TEXT NOT NULL,
    uid_number INTEGER NOT NULL,
    status INTEGER NOT NULL,
    PRIMARY KEY (email_name)
);
COMMIT;
"""

sqlite_db_path = '/var/lib/postfix/freedombox-aliases/aliases.sqlite3'


@contextlib.contextmanager
def db_cursor():
    # Turn ON autocommit mode
    con = sqlite3.connect(sqlite_db_path, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        yield cur
    finally:
        con.close()


def get(uid_number):
    s = 'SELECT * FROM Alias WHERE uid_number=?'
    with db_cursor() as cur:
        rows = cur.execute(s, (uid_number, ))
        result = [models.Alias(**r) for r in rows]
        return result


def exists(email_name):
    """Return whether alias is already taken."""
    try:
        pwd.getpwnam(email_name)
        return True
    except KeyError:
        pass

    with db_cursor() as cur:
        query = 'SELECT COUNT(*) FROM Alias WHERE email_name=?'
        cur.execute(query, (email_name, ))
        return cur.fetchone()[0] != 0


def put(uid_number, email_name):
    s = """INSERT INTO Alias(email_name, uid_number, status)
    SELECT ?,?,? WHERE NOT EXISTS(
        SELECT 1 FROM Alias WHERE email_name=?
    )"""
    with db_cursor() as cur:
        cur.execute(s, (email_name, uid_number, 1, email_name))


def delete(uid_number, alias_list):
    s = 'DELETE FROM Alias WHERE uid_number=? AND email_name=?'
    parameter_seq = ((uid_number, a) for a in alias_list)
    with db_cursor() as cur:
        cur.execute('BEGIN')
        cur.executemany(s, parameter_seq)
        cur.execute('COMMIT')


def set_enabled(uid_number, alias_list):
    return _set_status(uid_number, alias_list, 1)


def set_disabled(uid_number, alias_list):
    return _set_status(uid_number, alias_list, 0)


def _set_status(uid_number, alias_list, status):
    s = 'UPDATE Alias SET status=? WHERE uid_number=? AND email_name=?'
    parameter_seq = ((status, uid_number, a) for a in alias_list)
    with db_cursor() as cur:
        cur.execute('BEGIN')
        cur.executemany(s, parameter_seq)
        cur.execute('COMMIT')


def first_setup():
    actions.superuser_run('email_server', ['-i', 'aliases', 'setup'])
    _create_db_schema_if_not_exists()


def _create_db_schema_if_not_exists():
    # Create schema if not exists
    with db_cursor() as cur:
        cur.executescript(map_db_schema_script)
