#!/usr/bin/python3
# -*- mode: python -*-
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
Set required permissions for user "plinth" to run plinth in the development
environment.
"""

import augeas

sudoers_file = '/etc/sudoers.d/plinth'
aug = augeas.Augeas(
    flags=augeas.Augeas.NO_LOAD + augeas.Augeas.NO_MODL_AUTOLOAD)

# lens for shell-script config file
aug.set('/augeas/load/Shellvars/lens', 'Sudoers.lns')
aug.set('/augeas/load/Shellvars/incl[last() + 1]', sudoers_file)
aug.load()

aug.set('/files{}/spec[1]/host_group/command[2]'.format(sudoers_file),
        '/vagrant/actions/*')
aug.set('/files{}/spec[1]/host_group/command[1]/tag[2]'.format(sudoers_file),
        'SETENV')
aug.save()
