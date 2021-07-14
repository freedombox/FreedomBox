"""Manages email aliases"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import contextlib
import dbm
import logging
import os
import pwd
import sqlite3

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from plinth.modules.email_server import lock
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

mailsrv_dir = '/var/lib/plinth/mailsrv'
hash_db_path = mailsrv_dir + '/aliases'
sqlite_db_path = mailsrv_dir + '/aliases.sqlite3'

alias_sync_mutex = lock.Mutex('alias-sync')
logger = logging.getLogger(__name__)


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
        rows = cur.execute(s, (uid_number,))
        result = [models.Alias(**r) for r in rows]
        return result


def put(uid_number, email_name):
    s = """INSERT INTO Alias(email_name, uid_number, status)
    SELECT ?,?,? WHERE NOT EXISTS(
        SELECT 1 FROM Alias WHERE email_name=?
    )"""
    email_name = models.sanitize_email_name(email_name)
    # email_name cannot be the same as a user name
    try:
        pwd.getpwnam(email_name)
        raise ValidationError(_('The alias was taken'))
    except KeyError:
        pass

    with db_cursor() as cur:
        cur.execute(s, (email_name, uid_number, 1, email_name))
        if cur.rowcount == 0:
            raise ValidationError(_('The alias was taken'))

    schedule_hash_update()


def delete(uid_number, alias_list):
    s = 'DELETE FROM Alias WHERE uid_number=? AND email_name=?'
    for i in range(len(alias_list)):
        alias_list[i] = models.sanitize_email_name(alias_list[i])

    parameter_seq = ((uid_number, a) for a in alias_list)
    with db_cursor() as cur:
        cur.execute('BEGIN')
        cur.executemany(s, parameter_seq)
        cur.execute('COMMIT')
    schedule_hash_update()


def set_enabled(uid_number, alias_list):
    return _set_status(uid_number, alias_list, 1)


def set_disabled(uid_number, alias_list):
    return _set_status(uid_number, alias_list, 0)


def _set_status(uid_number, alias_list, status):
    s = 'UPDATE Alias SET status=? WHERE uid_number=? AND email_name=?'
    for i in range(len(alias_list)):
        alias_list[i] = models.sanitize_email_name(alias_list[i])

    parameter_seq = ((status, uid_number, a) for a in alias_list)
    with db_cursor() as cur:
        cur.execute('BEGIN')
        cur.executemany(s, parameter_seq)
        cur.execute('COMMIT')
    schedule_hash_update()


def schedule_hash_update():
    tmp = hash_db_path + '-tmp'
    with alias_sync_mutex.lock_all(), db_cursor() as cur:
        all_aliases = cur.execute('SELECT * FROM Alias')

        # Delete the temp file if exists
        if os.path.exists(tmp):
            os.unlink(tmp)

        # Create new alias db at temp path
        db = dbm.ndbm.open(tmp, 'c')
        try:
            for row in all_aliases:
                alias = models.Alias(**row)
                key = alias.email_name.encode('ascii') + b'\0'
                if alias.enabled:
                    value = str(alias.uid_number).encode('ascii') + b'\0'
                else:
                    value = b'/dev/null\0'
                db[key] = value
        finally:
            db.close()

        # Atomically replace old alias db, rename(2)
        os.rename(tmp + '.db', hash_db_path + '.db')


def first_setup():
    _create_db_schema_if_not_exists()
    schedule_hash_update()


def _create_db_schema_if_not_exists():
    # Create folder
    if not os.path.isdir(mailsrv_dir):
        os.mkdir(mailsrv_dir)
    # Create schema if not exists
    with db_cursor() as cur:
        cur.executescript(map_db_schema_script)

