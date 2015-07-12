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
    """Return whether a service is currently running.

    Does not need to run as root.
    """
    try:
        subprocess.check_output(['systemctl', 'status', servicename])
        return True
    except subprocess.CalledProcessError:
        # If a service is not running we get a status code != 0 and
        # thus a CalledProcessError
        return False


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
    service_start(service_name)


def service_disable(service_name):
    """Disable and stop service in systemd and sysvinit using update-rc.d."""
    try:
        service_stop(service_name)
    except subprocess.CalledProcessError:
        pass
    subprocess.call(['systemctl', 'disable', service_name])


def service_start(service_name):
    """Start a service."""
    subprocess.call(['systemctl', 'start', service_name])


def service_stop(service_name):
    """Stop a service."""
    subprocess.call(['systemctl', 'stop', service_name])


def service_restart(service_name):
    """Restart service with systemd."""
    subprocess.call(['systemctl', 'restart', service_name])


def service_reload(service_name):
    """Reload service with systemd."""
    subprocess.call(['systemctl', 'reload', service_name])
