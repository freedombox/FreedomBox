# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privileged actions to setup users' dovecot mail home directory."""

import subprocess

from plinth import actions


def setup():
    """Set correct permissions on /var/mail/ directory.

    For each user, /var/mail/<user> is the 'dovecot mail home' for that user.
    Dovecot creates new directories with the same permissions as the parent
    directory. Ensure that 'others' can access /var/mail/.

    """
    actions.superuser_run('email', ['home', 'setup'])


def action_setup():
    """Run chmod on /var/mail to remove all permissions for 'others'."""
    subprocess.run(['chmod', 'o-rwx', '/var/mail'], check=True)
