# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configuration for running tests.

To customize these settings, create a 'config_local.py' and override
the variables defined here.
"""

# When credentials are given, backups_ssh_path will be mounted.  In the given
# folder, repositories will be created in subfolders with random uuids.
backups_ssh_path = None
# provide backups_ssh_path and either a password or a keyfile for ssh tests
backups_ssh_password = None
backups_ssh_keyfile = None
backups_ssh_repo_uuid = 'plinth_test_sshfs'  # will be mounted to /media/<uuid>

# Import config_local to override the default variables
try:
    from .config_local import *  # noqa, pylint: disable=unused-import
except ImportError:
    pass
