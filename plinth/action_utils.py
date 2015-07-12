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


def webserver_is_enabled(name, kind='config'):
    """Return whether a config/module/site is enabled in Apache."""
    option_map = {'config': '-c', 'site': '-s', 'module': '-m'}
    try:
        # Don't print anything on the terminal
        subprocess.check_output(['a2query', option_map[kind], name],
                                stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False


def webserver_enable(name, kind='config', apply_changes=True):
    """Enable a config/module/site in Apache.

    Restart/reload the webserver if apply_changes is True.  Return
    whether restart(True) or reload(False) is required.  If changes
    have been applied, return None.
    """
    command_map = {'config': 'a2enconf',
                   'site': 'a2ensite',
                   'module': 'a2enmod'}
    subprocess.check_output([command_map[kind], name])

    if not apply_changes:
        return kind == 'module'

    if kind == 'module':
        service_restart('apache2')
    else:
        service_reload('apache2')


def webserver_disable(name, kind='config', apply_changes=True):
    """Disable config/module/site in Apache.

    Restart/reload the webserver if apply_changes is True.  Return
    whether restart(True) or reload(False) is required.  If changes
    have been applied, return None.
    """
    command_map = {'config': 'a2disconf',
                   'site': 'a2dissite',
                   'module': 'a2dismod'}
    subprocess.check_output([command_map[kind], name])

    if not apply_changes:
        return kind == 'module'

    if kind == 'module':
        service_restart('apache2')
    else:
        service_reload('apache2')


class WebserverChange(object):
    """Context to restart/reload Apache after configuration changes."""

    def __init__(self):
        """Initialize the context object state."""
        self.restart_required = False

    def __enter__(self):
        """Return the context object so methods could be called on it."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Restart or reload the webserver.

        Don't supress exceptions.  If an exception occurs
        restart/reload the webserver based on enable/disable
        operations done so far.
        """
        if self.restart_required:
            service_restart('apache2')
        else:
            service_reload('apache2')


    def enable(self, name, kind='config'):
        """Enable a config/module/site in Apache.

        Don't apply the changes until the context is exited.
        """
        restart_required = webserver_enable(name, kind, apply_changes=False)
        self.restart_required = self.restart_required or restart_required

    def disable(self, name, kind='config'):
        """Disable a config/module/site in Apache.

        Don't apply the changes until the context is exited.
        """
        restart_required = webserver_disable(name, kind, apply_changes=False)
        self.restart_required = self.restart_required or restart_required
