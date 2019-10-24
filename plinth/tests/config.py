#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
