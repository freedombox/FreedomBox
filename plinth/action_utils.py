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

import os
import logging
import shutil
import socket
import subprocess
import tempfile
import psutil

from django.utils.translation import ugettext as _

logger = logging.getLogger(__name__)


def is_systemd_running():
    """Return if we are running under systemd."""
    return os.path.exists('/run/systemd')


def service_is_running(servicename):
    """Return whether a service is currently running.

    Does not need to run as root.
    """
    try:
        if is_systemd_running():
            subprocess.run(
                ['systemctl', 'status', servicename],
                check=True,
                stdout=subprocess.DEVNULL)
        else:
            subprocess.run(
                ['service', servicename, 'status'],
                check=True,
                stdout=subprocess.DEVNULL)

        return True
    except subprocess.CalledProcessError:
        # If a service is not running we get a status code != 0 and
        # thus a CalledProcessError
        return False


def service_is_enabled(service_name):
    """Check if service is enabled in systemd."""
    try:
        subprocess.run(
            ['systemctl', 'is-enabled', service_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
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
    """Start a service with systemd or sysvinit."""
    if is_systemd_running():
        subprocess.run(
            ['systemctl', 'start', service_name], stdout=subprocess.DEVNULL)
    else:
        subprocess.run(
            ['service', service_name, 'start'], stdout=subprocess.DEVNULL)


def service_stop(service_name):
    """Stop a service with systemd or sysvinit."""
    if is_systemd_running():
        subprocess.run(
            ['systemctl', 'stop', service_name], stdout=subprocess.DEVNULL)
    else:
        subprocess.run(
            ['service', service_name, 'stop'], stdout=subprocess.DEVNULL)


def service_restart(service_name):
    """Restart a service with systemd or sysvinit."""
    if is_systemd_running():
        subprocess.run(
            ['systemctl', 'restart', service_name], stdout=subprocess.DEVNULL)
    else:
        subprocess.run(
            ['service', service_name, 'restart'], stdout=subprocess.DEVNULL)


def service_reload(service_name):
    """Reload a service with systemd or sysvinit."""
    if is_systemd_running():
        subprocess.run(
            ['systemctl', 'reload', service_name], stdout=subprocess.DEVNULL)
    else:
        subprocess.run(
            ['service', service_name, 'reload'], stdout=subprocess.DEVNULL)


def webserver_is_enabled(name, kind='config'):
    """Return whether a config/module/site is enabled in Apache."""
    if not shutil.which('a2query'):
        return False

    option_map = {'config': '-c', 'site': '-s', 'module': '-m'}
    try:
        # Don't print anything on the terminal
        subprocess.check_output(
            ['a2query', option_map[kind], name], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False


def webserver_enable(name, kind='config', apply_changes=True):
    """Enable a config/module/site in Apache.

    Restart/reload the webserver if apply_changes is True.  Return
    whether restart('restart'), reload('reload') or no action (None)
    is required.  If changes have been applied, then performed action
    is returned.
    """
    if webserver_is_enabled(name, kind):
        return

    command_map = {
        'config': 'a2enconf',
        'site': 'a2ensite',
        'module': 'a2enmod'
    }
    subprocess.check_output([command_map[kind], name])

    action_required = 'restart' if kind == 'module' else 'reload'

    if apply_changes:
        if action_required == 'restart':
            service_restart('apache2')
        else:
            service_reload('apache2')

    return action_required


def webserver_disable(name, kind='config', apply_changes=True):
    """Disable config/module/site in Apache.

    Restart/reload the webserver if apply_changes is True.  Return
    whether restart('restart'), reload('reload') or no action (None)
    is required.  If changes have been applied, then performed action
    is returned.
    """
    if not webserver_is_enabled(name, kind):
        return

    command_map = {
        'config': 'a2disconf',
        'site': 'a2dissite',
        'module': 'a2dismod'
    }
    subprocess.check_output([command_map[kind], name])

    action_required = 'restart' if kind == 'module' else 'reload'

    if apply_changes:
        if action_required == 'restart':
            service_restart('apache2')
        else:
            service_reload('apache2')

    return action_required


class WebserverChange(object):
    """Context to restart/reload Apache after configuration changes."""

    def __init__(self):
        """Initialize the context object state."""
        self.actions_required = set()

    def __enter__(self):
        """Return the context object so methods could be called on it."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Restart or reload the webserver.

        Don't supress exceptions.  If an exception occurs
        restart/reload the webserver based on enable/disable
        operations done so far.
        """
        if 'restart' in self.actions_required:
            service_restart('apache2')
        elif 'reload' in self.actions_required:
            service_reload('apache2')

    def enable(self, name, kind='config'):
        """Enable a config/module/site in Apache.

        Don't apply the changes until the context is exited.
        """
        action_required = webserver_enable(name, kind, apply_changes=False)
        self.actions_required.add(action_required)

    def disable(self, name, kind='config'):
        """Disable a config/module/site in Apache.

        Don't apply the changes until the context is exited.
        """
        action_required = webserver_disable(name, kind, apply_changes=False)
        self.actions_required.add(action_required)


def diagnose_port_listening(port, kind='tcp', listen_address=None):
    """Run a diagnostic on whether a port is being listened on.

    Kind must be one of inet, inet4, inet6, tcp, tcp4, tcp6, udp,
    udp4, udp6, unix, all.  See psutil.net_connection() for more
    information.
    """
    result = _check_port(port, kind, listen_address)

    if listen_address:
        test = _('Listening on {kind} port {listen_address}:{port}') \
               .format(kind=kind, listen_address=listen_address, port=port)
    else:
        test = _('Listening on {kind} port {port}') \
               .format(kind=kind, port=port)

    return [test, 'passed' if result else 'failed']


def _check_port(port, kind='tcp', listen_address=None):
    """Return whether a port is being listened on."""
    run_kind = kind

    if kind == 'tcp4':
        run_kind = 'tcp'

    if kind == 'udp4':
        run_kind = 'udp'

    for connection in psutil.net_connections(run_kind):
        # TCP connections must have status='listen'
        if kind in ('tcp', 'tcp4', 'tcp6') and \
           connection.status != psutil.CONN_LISTEN:
            continue

        # UDP connections must have empty remote address
        if kind in ('udp', 'udp4', 'udp6') and \
           connection.raddr != ():
            continue

        # Port should match
        if connection.laddr[1] != port:
            continue

        # Listen address if requested should match
        if listen_address and connection.laddr[0] != listen_address:
            continue

        # Special additional checks only for IPv4
        if kind != 'tcp4' and kind != 'udp4':
            return True

        # Found socket is IPv4
        if connection.family == socket.AF_INET:
            return True

        # Full IPv6 address range includes mapped IPv4 address also
        if connection.laddr[0] == '::':
            return True

    return False


def diagnose_url(url,
                 kind=None,
                 env=None,
                 check_certificate=True,
                 extra_options=None,
                 wrapper=None,
                 expected_output=None):
    """Run a diagnostic on whether a URL is accessible.

    Kind can be '4' for IPv4 or '6' for IPv6.
    """
    command = ['curl', '-f', '-w', '%{response_code}', url]

    if wrapper:
        command.insert(0, wrapper)

    if not check_certificate:
        command.append('-k')

    if extra_options:
        command.extend(extra_options)

    if kind:
        command.append({'4': '-4', '6': '-6'}[kind])

    try:
        process = subprocess.run(
            command,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        result = 'passed'
        if expected_output and expected_output not in process.stdout.decode():
            result = 'failed'
    except subprocess.CalledProcessError as exception:
        result = 'failed'
        # Authorization failed is a success
        if exception.stdout.decode().strip() in ('401', '405'):
            result = 'passed'
    except FileNotFoundError:
        result = 'error'

    if kind:
        return [
            _('Access URL {url} on tcp{kind}').format(url=url, kind=kind),
            result
        ]
    else:
        return [_('Access URL {url}').format(url=url), result]


def diagnose_url_on_all(url, **kwargs):
    """Run a diagnostic on whether a URL is accessible."""
    results = []
    for address in get_addresses():
        current_url = url.format(host=address['url_address'])
        results.append(
            diagnose_url(current_url, kind=address['kind'], **kwargs))

    return results


def diagnose_netcat(host, port, input='', negate=False):
    """Run a diagnostic using netcat."""
    try:
        process = subprocess.Popen(
            ['nc', host, str(port)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.communicate(input=input.encode())
        if process.returncode != 0:
            result = 'failed'
        else:
            result = 'passed'
    except Exception:
        result = 'failed'

    test = _('Connect to {host}:{port}')
    if negate:
        result = 'failed' if result == 'passed' else 'passed'
        test = _('Cannot connect to {host}:{port}')

    return [test.format(host=host, port=port), result]


def get_addresses():
    """Return a list of IP addreses and hostnames."""
    addresses = get_ip_addresses()

    hostname = get_hostname()
    addresses.append({
        'kind': '4',
        'address': 'localhost',
        'numeric': False,
        'url_address': 'localhost'
    })
    addresses.append({
        'kind': '6',
        'address': 'localhost',
        'numeric': False,
        'url_address': 'localhost'
    })
    addresses.append({
        'kind': '4',
        'address': hostname,
        'numeric': False,
        'url_address': hostname
    })

    # XXX: When a hostname is resolved to IPv6 address, it may likely
    # be link-local address.  Link local IPv6 addresses are valid only
    # for a given link and need to be scoped with interface name such
    # as '%eth0' to work.  Tools such as curl don't seem to handle
    # this correctly.
    # addresses.append({'kind': '6', 'address': hostname, 'numeric': False})

    return addresses


def get_ip_addresses():
    """Return a list of IP addresses assigned to the system."""
    addresses = []

    output = subprocess.check_output(['ip', '-o', 'addr'])
    for line in output.decode().splitlines():
        parts = line.split()
        address = {
            'kind': '4' if parts[2] == 'inet' else '6',
            'address': parts[3].split('/')[0],
            'url_address': parts[3].split('/')[0],
            'numeric': True,
            'scope': parts[5],
            'interface': parts[1]
        }

        if address['kind'] == '6' and address['numeric']:
            if address['scope'] != 'link':
                address['url_address'] = '[{0}]'.format(address['address'])
            else:
                address['url_address'] = '[{0}%{1}]'.format(
                    address['url_address'], address['interface'])

        addresses.append(address)

    return addresses


def get_hostname():
    """Return the current hostname."""
    return subprocess.check_output(['hostname']).decode().strip()


def dpkg_reconfigure(package, config):
    """Reconfigure package using debconf database override."""
    override_template = '''
Name: {package}/{key}
Template: {package}/{key}
Value: {value}
Owners: {package}
'''
    override_data = ''
    for key, value in config.items():
        override_data += override_template.format(
            package=package, key=key, value=value)

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as override_file:
        override_file.write(override_data)

    env = os.environ.copy()
    env['DEBCONF_DB_OVERRIDE'] = 'File{' + override_file.name + \
                                 ' readonly:true}'
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    subprocess.run(['dpkg-reconfigure', package], env=env)

    try:
        os.remove(override_file.name)
    except OSError:
        pass
