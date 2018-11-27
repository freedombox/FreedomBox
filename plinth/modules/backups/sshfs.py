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
Utilities to work with sshfs.
"""

import json

from plinth.modules.backups import run


def mount(remote_path, mountpoint, access_params):
    run(['mount', '--mountpoint', mountpoint, '--path', remote_path],
        access_params)


def umount(mountpoint):
    run(['umount', '--mountpoint', mountpoint])


def is_mounted(mountpoint):
    output = run(['is-mounted', '--mountpoint', mountpoint])
    return json.loads(output)
