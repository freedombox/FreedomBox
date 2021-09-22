# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Custom password hashers suitable for home servers.
"""

from django.contrib.auth.hashers import Argon2PasswordHasher


class Argon2PasswordHasherLowMemory(Argon2PasswordHasher):
    """Argon2 password hasher that uses less CPU and RAM than Django's default.

    Derive from and override the default complexity parameters for Django. In
    Django 2.2, the defaults are time: 2, memory: 512 and parallelism: 2. In
    Django 3.2, the defaults are time: 2, memory: 102400, parallelism: 8. This
    takes more than 3 seconds per verification on a Lime2 board.

    On a Pioneer Edition, Olimex Lime2 board, the selected parameters result in
    about 200ms for password verification:

    $ python3 -m argon2 -p 2 -m 4096
    Running Argon2id 100 times with:
    hash_len: 16 bytes
    memory_cost: 4096 KiB
    parallelism: 2 threads
    time_cost: 2 iterations

    Measuring...

    2.17e+02ms per password verification

    """
    time_cost = 2  # Iterations
    memory_cost = 4096  # KiB
    parallelism = 2  # Threads
