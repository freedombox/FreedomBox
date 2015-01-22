#!/usr/bin/python3
# -*- mode: python -*-
#
# This file is part of Plinth.
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
Python action utility functions
"""

import subprocess

def is_running(servicename):
    """Evaluates whether a service is currently running. Returns boolean"""
    try:
        output = subprocess.check_output(['service', servicename, 'status'])
    except subprocess.CalledProcessError:
        # Usually if a service is not running we get a status code != 0 and
        # thus a CalledProcessError
        return False
    else:
        running = False # default value
        for line in output.decode('utf-8').split('\n'):
            if 'Active' in line and 'running' in line:
                running = True
                break
        return running
