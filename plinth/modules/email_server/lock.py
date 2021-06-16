# SPDX-License-Identifier: AGPL-3.0-or-later
import contextlib
import fcntl
import os
import threading


class Mutex:
    """File and pthread lock based resource mutex"""

    def __init__(self, lock_file):
        self.thread_mutex = threading.Lock()
        self.lock_path = '/var/lock/' + lock_file

    @contextlib.contextmanager
    def lock_threads_only(self):
        """Acquire the thread lock but not the file lock"""
        self.thread_mutex.acquire(timeout=5)
        try:
            yield
        finally:
            self.thread_mutex.release()

    @contextlib.contextmanager
    def lock_all(self):
        """Acquire both the thread lock and the file lock"""
        with self.lock_threads_only():
            fd = open(self.lock_path, 'wb')
            # FIXME: Who can lock?
            try:
                os.fchmod(fd.fileno(), 0o666)  # rw-rw-rw-
            except OSError:
                pass
            fcntl.lockf(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.lockf(fd, fcntl.LOCK_UN)
                fd.close()
