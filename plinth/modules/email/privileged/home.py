# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Privileged actions to setup users' dovecot mail home directory.

See:
https://doc.dovecot.org/configuration_manual/authentication/user_databases_userdb/
"""

import subprocess

from plinth.actions import privileged


@privileged
def setup_home():
    """Set correct permissions on /var/mail/ directory.

    For each user, /var/mail/<user> is the 'dovecot mail home' for that user.
    Dovecot creates new directories with the same permissions as the parent
    directory. Ensure that 'others' can't access /var/mail/.
    """
    subprocess.run(['chmod', 'o-rwx', '/var/mail'], check=True)
