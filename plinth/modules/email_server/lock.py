# SPDX-License-Identifier: AGPL-3.0-or-later
import contextlib
import errno
import fcntl
import logging
import os
import pwd
import threading
import time

logger = logging.getLogger(__name__)


class Mutex:
    """File and pthread lock based resource mutex"""

    def __init__(self, lock_file):
        self.thread_mutex = threading.Lock()
        self.lock_path = '/var/lock/' + lock_file

    @contextlib.contextmanager
    def lock_threads_only(self):
        """Acquire the thread lock but not the file lock"""
        if not self.thread_mutex.acquire(timeout=5):
            raise RuntimeError('Could not acquire thread lock')
        try:
            yield
        finally:
            self.thread_mutex.release()

    @contextlib.contextmanager
    def lock_all(self):
        """Acquire both the thread lock and the file lock"""
        with self.lock_threads_only():
            # Set up
            fd = self._open_lock_file()
            fcntl.lockf(fd, fcntl.LOCK_EX)
            self._chmod_and_chown(fd)
            # Enter context
            try:
                yield
            finally:
                # Clean up
                fcntl.lockf(fd, fcntl.LOCK_UN)
                fd.close()

    def _open_lock_file(self):
        """Attempt to open lock file for R&W. Raises OSError on failure"""
        attempts = 10
        errno = -1
        fd = None
        # Simulate a spin lock
        while attempts > 0:
            errno, fd = self._try(lambda: open(self.lock_path, 'wb'))
            if errno == 0:
                return fd
            else:
                attempts -= 1
                time.sleep(0.25)
        raise OSError(errno, os.strerror(errno))

    def _chmod_and_chown(self, fd):
        """If the process UID is root, set fd's mode and ownership to
        appropriate values. If we are not root, only set the mode"""
        if os.getuid() == 0:
            user_info = pwd.getpwnam('plinth')
            os.fchown(fd.fileno(), 0, 0)
            os.fchmod(fd.fileno(), 0o660)  # rw-rw----
            fd.truncate(0)
            os.fchown(fd.fileno(), user_info.pw_uid, user_info.pw_gid)
        else:
            errno, _ = self._try(lambda: os.fchmod(fd.fileno(), 0o660))
            if errno != 0:
                logger.warning('chmod failed, lock path %s, errno %d',
                               self.lock_path, errno)

    def _try(self, function):
        try:
            return 0, function()
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EPERM):
                return error.errno, None
            else:
                raise
