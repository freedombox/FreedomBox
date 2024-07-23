# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common utilities to help with handling a database.
"""

import pathlib
import subprocess
import threading
from typing import ClassVar


class DBLock:
    """A re-entrant lock with a fixed timeout (not -1) by default."""

    TIMEOUT: ClassVar[float] = 30

    def __init__(self, *args, **kwargs):
        """Create an RLock object."""
        self._lock = threading.RLock(*args, **kwargs)
        self.timeout = DBLock.TIMEOUT

    def __getattr__(self, name):
        """Return RLock attributes."""
        return getattr(self._lock, name)

    def __enter__(self):
        """Use RLock context management."""
        return self._lock.acquire(timeout=self.timeout)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Use RLock context management."""
        try:
            self._lock.release()
        except RuntimeError:
            # Lock was not acquired
            pass


# The Problem
# -----------
# Since this is a small application (in terms of data stored and requests per
# second handled), we use sqlite3 as the backend database. This gives us more
# reliability. However, sqlite3 has limited capability to handle parallel
# requests. When we try to use multiple Model.update_or_create() calls
# simultaneously, only the first one succeeds and the remaining fail with
# 'Database is locked' errors.
#
# The 'timeout' value passed during connection creation means that queries will
# wait for a maximum of given timeout period when trying to acquire locks.
# However, in some cases, to prevent deadlocks caused by threads waiting on
# each other, sqlite3 will not wait and immediately throw an exception.
#
# If we set the isolation level to 'EXCLUSIVE' or 'IMMEDIATE' instead of the
# default 'DEFERRED', each transaction should acquire a write lock immediately
# after transaction is started. This reduces the situations in which threads
# deadlock on each other. This improves the situation somewhat. However, this
# is still causing immediate timeout errors due to the way Django does its
# update_or_create() queries.
#
# This is true even in 'WAL' (write-ahead-log) journaling mode. While WAL mode
# makes it easier to have many read transactions while one write query is
# happening, it does not prevent this situation.
#
# Django should ideally provide a way to serialize these queries specifically
# to work with sqlite3 locking behavior. There seems to be no such way
# currently.
#
# Workaround
# ----------
# To workaround the problem, use a simple lock to serialize all database
# queries. Like this:
#
# with db.lock:
#     # do some short database operation
#
# Queries usually have short execution time (unless stuck on disk I/O). A lot
# of parallel request processing is not expected from this service. We want
# more reliability (not failing on DB locks) over the ability to run parallel
# requests. Typically, requests waiting to perform DB queries will only have to
# wait < 1 second to get their turn. In the worst case, the database lock will
# not be acquired and the code continues to anyway.
#
# This locking can't be done in all situations. For example, queries made
# within Django framework are not locked. Still, this approach should prevent
# most of the significant cases where we have seen database lock issues.

lock = DBLock()


#
# PostgreSQL utilites
#
def _run_as_postgres(command, stdin=None, stdout=None):
    """Run a command as postgres user."""
    command = ['sudo', '--user', 'postgres'] + command
    return subprocess.run(command, stdin=stdin, stdout=stdout, check=True)


def postgres_dump_database(backup_file: str, database_name: str,
                           database_user: str):
    """Dump PostgreSQL database to a file.

    Overwrites file if it exists. Uses pg_dump utility from postgres package
    (needs to be installed).
    """
    backup_path = pathlib.Path(backup_file)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with open(backup_path, 'w', encoding='utf-8') as file_handle:
        process = _run_as_postgres(['pg_dumpall', '--roles-only'],
                                   stdout=subprocess.PIPE)
        file_handle.write(f'DROP ROLE IF EXISTS {database_user};\n')
        for line in process.stdout.decode().splitlines():
            if database_user in line:
                file_handle.write(line + '\n')

    with open(backup_path, 'a', encoding='utf-8') as file_handle:
        _run_as_postgres(
            ['pg_dump', '--create', '--clean', '--if-exists', database_name],
            stdout=file_handle)


def postgres_restore_database(backup_file: str, database_name):
    """Restore PostgreSQL database from a file.

    Drops database and recreates it. Uses pg_dump utility from postgres package
    (needs to be installed).
    """
    # This is needed for old backups only. New backups include 'DROP DATABASE
    # IF EXISTS' and 'CREATE DATABASE' statements.
    _run_as_postgres(['dropdb', database_name])
    _run_as_postgres(['createdb', database_name])

    with open(backup_file, 'r', encoding='utf-8') as file_handle:
        _run_as_postgres(['psql', '--dbname', database_name],
                         stdin=file_handle)
