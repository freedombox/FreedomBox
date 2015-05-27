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
Python action utility functions.
"""

import subprocess


def service_is_running(servicename):
    """Evaluates whether a service is currently running. Returns boolean"""
    try:
        output = subprocess.check_output(['service', servicename, 'status'])
    except subprocess.CalledProcessError:
        # Usually if a service is not running we get a status code != 0 and
        # thus a CalledProcessError
        return False
    else:
        running = False  # default value
        for line in output.decode('utf-8').split('\n'):
            if 'Active' in line and 'running' in line:
                running = True
                break
        return running


def service_is_enabled(service_name):
    """Check if service is enabled in systemd."""
    try:
        subprocess.check_output(['systemctl', 'is-enabled', service_name])
        return True
    except subprocess.CalledProcessError:
        return False


def service_enable(service_name):
    """Enable and start a service in systemd and sysvinit using update-rc.d."""
    subprocess.call(['systemctl', 'enable', service_name])
    subprocess.call(['systemctl', 'start', service_name])


def service_disable(service_name):
    """Disable and stop service in systemd and sysvinit using update-rc.d."""
    subprocess.call(['systemctl', 'stop', service_name])
    subprocess.call(['systemctl', 'disable', service_name])


def service_restart(service_name):
    """Restart service with systemd."""
    subprocess.call(['systemctl', 'restart', service_name])
