#!/usr/bin/python3
import fcntl

def is_dpkg_active():
    """
    Check whether ``apt-get`` or ``dpkg`` is currently active.

    This works by checking whether the lock file ``/var/lib/dpkg/lock`` is
    locked by an ``apt-get`` or ``dpkg`` process, which in turn is done by
    momentarily trying to acquire the lock. This means that the current process
    needs to have sufficient privileges.

    :returns: ``True`` when the lock is already taken (``apt-get`` or ``dpkg``
              is running), ``False`` otherwise.
    :raises: :py:exc:`exceptions.IOError` if the required privileges are not
             available.

    .. note:: ``apt-get`` doesn't acquire this lock until it needs it, for
              example an ``apt-get update`` run consists of two phases (first
              fetching updated package lists and then updating the local
              package index) and only the second phase claims the lock (because
              the second phase writes the local package index which is also
              read from and written to by ``dpkg``).
    """
    with open('/var/lib/dpkg/lock', 'w') as handle:
        try:
            fcntl.lockf(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print("False")
            return False
        except IOError:
            print("True")
            return True

if __name__ == "__main__":
    is_dpkg_active()
