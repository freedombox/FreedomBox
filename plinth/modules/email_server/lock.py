# SPDX-License-Identifier: AGPL-3.0-or-later
import contextlib
import errno
import fcntl
import logging
import os
import pwd
import subprocess
import threading

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
            # Enter context
            try:
                yield
            finally:
                # Clean up
                fcntl.lockf(fd, fcntl.LOCK_UN)
                fd.close()

    def _open_lock_file(self):
        """Attempt to open lock file for R&W. Raises OSError on failure"""
        if os.getuid() == 0:
            if os.path.exists(self.lock_path):
                # Check its owner and mode
                stat = os.stat(self.lock_path)
                owner = pwd.getpwuid(stat.st_uid).pw_name
                mode = stat.st_mode & 0o777
                if owner != 'plinth' or mode != 0o600:
                    logger.warning('Clean up bad file %s', self.lock_path)
                    os.unlink(self.lock_path)
                    self._create_lock_file_as_plinth()
            else:
                self._create_lock_file_as_plinth()

        return open(self.lock_path, 'wb+')

    def _create_lock_file_as_plinth(self):
        args = ['sudo', '-n', '-u', 'plinth', 'touch', self.lock_path]
        completed = subprocess.run(args, capture_output=True)
        if completed.returncode != 0:
            logger.critical('Process returned %d', completed.returncode)
            logger.critical('Stdout: %r', completed.stdout)
            logger.critical('Stderr: %r', completed.stderr)
            raise OSError('Could not create ' + self.lock_path)
        os.chmod(self.lock_path, 0o600)

    def _try(self, function):
        try:
            return 0, function()
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EPERM):
                return error.errno, None
            else:
                raise
