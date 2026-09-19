# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for database utilities.
"""
import threading
import time

from .. import db
from ..db import dbconfig


def test_db_lock_no_wait():
    """Test that lock is immediately by first user."""
    lock = db.DBLock()

    start_time = time.time()
    with lock:
        pass

    end_time = time.time()
    assert end_time - start_time < 0.1


def test_db_lock_max_wait():
    """Test that lock waits only for timeout period."""
    event = threading.Event()
    lock = db.DBLock()
    lock.timeout = 0.25

    def thread_func():
        with lock:
            event.set()
            time.sleep(0.3)

    thread = threading.Thread(target=thread_func)
    thread.start()

    event.wait()
    start_time = time.time()
    with lock as return_value:
        pass

    end_time = time.time()
    assert end_time - start_time < 0.27
    assert not return_value


def test_db_lock_release():
    """Test that lock is available after release."""
    event = threading.Event()
    lock = db.DBLock()
    lock.timeout = 0.25

    def thread_func():
        with lock:
            event.set()
            time.sleep(0.2)

    thread = threading.Thread(target=thread_func)
    thread.start()

    event.wait()
    start_time = time.time()
    with lock as return_value:
        pass

    end_time = time.time()
    assert return_value
    assert end_time - start_time <= 0.23


def test_dbconfig_get_credentials(tmp_path):
    """Test that parsing a dbconfig-common file works."""
    file_path = tmp_path / 'test.conf'
    configuration = '''
dbc_dbserver='localhost'
dbc_dbname='miniflux'
dbc_dbuser='miniflux'
dbc_dbpass='gCcNyWjyPjDH'
'''
    file_path.write_text(configuration)
    credentials = dbconfig.get_credentials(file_path)
    assert credentials == {
        'host': 'localhost',
        'database': 'miniflux',
        'user': 'miniflux',
        'password': 'gCcNyWjyPjDH',
    }
