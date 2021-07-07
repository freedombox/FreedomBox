# SPDX-License-Identifier: AGPL-3.0-or-later
import contextlib
import fcntl
import logging
import os
import pwd
import re
import subprocess
import threading

lock_name_pattern = re.compile('^[0-9a-zA-Z_-]+$')
logger = logging.getLogger(__name__)


class RaceCondition(AssertionError):
    pass


class Mutex:
    """File and pthread lock based resource mutex"""

    def __init__(self, lock_name):
        if not lock_name_pattern.match(lock_name):
            raise ValueError('Bad lock name')
        self._lock_path = '/var/lock/plinth-%s.lock' % lock_name
        self._thread_mutex = threading.Lock()

    @property
    def lock_path(self):
        return self._lock_path

    @contextlib.contextmanager
    def lock_threads_only(self):
        """Acquire the thread lock but not the file lock"""
        if not self._thread_mutex.acquire(timeout=5):
            raise RuntimeError('Could not acquire thread lock')
        try:
            yield
        finally:
            self._thread_mutex.release()

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
        og_ruid, og_euid, og_suid = os.getresuid()
        if og_euid == 0 and threading.active_count() > 1:
            raise RaceCondition('setuid in a multi-threaded process')
        if not os.path.exists(self.lock_path):
            self._create_lock_file_as_plinth()

        fd = None
        try:
            if og_euid == 0:
                # Temporarily run the current process as plinth
                plinth_uid = pwd.getpwnam('plinth').pw_uid
                self._checked_setresuid(og_ruid, plinth_uid, 0)
            fd = open(self.lock_path, 'w+b')
        finally:
            # Restore resuid
            if og_euid == 0:
                self._checked_setresuid(og_ruid, 0, 0)
                if og_suid != 0:
                    self._checked_setresuid(og_ruid, 0, og_suid)

        return fd

    def _create_lock_file_as_plinth(self):
        # Don't change the current processes umask
        # Do create a new process
        args = ['sudo', '-n', '-u', 'plinth', '/bin/sh', '-c']
        args.append('umask 177 && > ' + self.lock_path)

        completed = subprocess.run(args, capture_output=True)
        if completed.returncode != 0:
            logger.critical('Subprocess returned %d', completed.returncode)
            logger.critical('Stdout: %r', completed.stdout)
            logger.critical('Stderr: %r', completed.stderr)
            raise OSError('Could not create ' + self.lock_path)

    def _checked_setresuid(self, ruid, euid, suid):
        os.setresuid(ruid, euid, suid)
        if os.getresuid() != (ruid, euid, suid):
            try:
                raise SystemExit('PANIC: setresuid failed')
            except SystemExit as e:
                # Print stack trace
                logger.exception(e)
                # Force exit
                exit(1)
