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

backups_ssh_path = None
backups_ssh_password = None
backups_ssh_keyfile = None
backups_ssh_mountpoint = '/mnt/plinth_test_sshfs'

# Import config_local to override the default variables
try:
    from config_local.py import *
except ImportError:
    pass
