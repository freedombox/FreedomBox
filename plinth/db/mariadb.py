# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities to help with MariaDB/MySQL databases.

Uses utilities from 'mysql-client' package such as 'mysql' and 'mysqldump'.
"""

import subprocess


def run_query(database_name: str, query: str) -> subprocess.CompletedProcess:
    """Run a database query using 'root' user.

    Does not ensure that the database server is running.
    """
    return subprocess.run(
        ['mysql', '--user=root', '--database', database_name],
        input=query.encode('utf-8'), check=True)
