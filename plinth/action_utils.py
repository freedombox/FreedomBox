# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Python action utility functions.
"""

import logging
import os
import pathlib
import shutil
import subprocess
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)

UWSGI_ENABLED_PATH = '/etc/uwsgi/apps-enabled/{config_name}.ini'
UWSGI_AVAILABLE_PATH = '/etc/uwsgi/apps-available/{config_name}.ini'

# Flag on disk to indicate if freedombox package was held by
# plinth. This is a backup in case the process is interrupted and hold
# is not released.
apt_hold_flag = pathlib.Path('/var/lib/freedombox/package-held')


def is_systemd_running():
    """Return if we are running under systemd."""
    return os.path.exists('/run/systemd')


def service_daemon_reload():
    """Reload systemd to ensure that newer unit files are read."""
    subprocess.run(['systemctl', 'daemon-reload'], check=True,
                   stdout=subprocess.DEVNULL)


def service_is_running(servicename):
    """Return whether a service is currently running.

    Does not need to run as root.
    """
    try:
        subprocess.run(['systemctl', 'status', servicename], check=True,
                       stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        # If a service is not running we get a status code != 0 and
        # thus a CalledProcessError
        return False


@contextmanager
def service_ensure_running(service_name):
    """Ensure a service is running and return to previous state."""
    starting_state = service_is_running(service_name)
    if not starting_state:
        service_enable(service_name)

    try:
        yield starting_state
    finally:
        if not starting_state:
            service_disable(service_name)


def service_is_enabled(service_name, strict_check=False):
    """Check if service is enabled in systemd.

    In some cases, after disabling a service, systemd puts it into a state
    called 'enabled-runtime' and returns a positive response to 'is-enabled'
    query. Until we understand better, a conservative work around is to pass
    strict=True to services effected by this behavior.

    """
    try:
        process = subprocess.run(['systemctl', 'is-enabled', service_name],
                                 check=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
        if not strict_check:
            return True

        return process.stdout.decode().strip() == 'enabled'
    except subprocess.CalledProcessError:
        return False


def service_enable(service_name):
    """Enable and start a service in systemd and sysvinit using update-rc.d."""
    subprocess.call(['systemctl', 'enable', service_name])
    service_start(service_name)


def service_disable(service_name):
    """Disable and stop service in systemd and sysvinit using update-rc.d."""
    subprocess.call(['systemctl', 'disable', service_name])
    try:
        service_stop(service_name)
    except subprocess.CalledProcessError:
        pass


def service_mask(service_name):
    """Mask a service"""
    subprocess.call(['systemctl', 'mask', service_name])


def service_unmask(service_name):
    """Unmask a service"""
    subprocess.call(['systemctl', 'unmask', service_name])


def service_start(service_name):
    """Start a service with systemd or sysvinit."""
    service_action(service_name, 'start')


def service_stop(service_name):
    """Stop a service with systemd or sysvinit."""
    service_action(service_name, 'stop')


def service_restart(service_name):
    """Restart a service with systemd or sysvinit."""
    service_action(service_name, 'restart')


def service_try_restart(service_name):
    """Try to restart a service with systemd or sysvinit."""
    service_action(service_name, 'try-restart')


def service_reload(service_name):
    """Reload a service with systemd or sysvinit."""
    service_action(service_name, 'reload')


def service_action(service_name, action):
    """Perform the given action on the service_name."""
    subprocess.run(['systemctl', action, service_name],
                   stdout=subprocess.DEVNULL, check=False)


def webserver_is_enabled(name, kind='config'):
    """Return whether a config/module/site is enabled in Apache."""
    if not shutil.which('a2query'):
        return False

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
    whether restart('restart'), reload('reload') or no action (None)
    is required.  If changes have been applied, then performed action
    is returned.
    """
    if webserver_is_enabled(name, kind) and kind == 'module':
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


class WebserverChange:
    """Context to restart/reload Apache after configuration changes."""

    def __init__(self):
        """Initialize the context object state."""
        self.actions_required = set()

    def __enter__(self):
        """Return the context object so methods could be called on it."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Restart or reload the webserver.

        Don't suppress exceptions.  If an exception occurs
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


def uwsgi_is_enabled(config_name):
    """Return whether a uwsgi config is enabled."""
    enabled_path = UWSGI_ENABLED_PATH.format(config_name=config_name)
    return os.path.exists(enabled_path)


def uwsgi_enable(config_name):
    """Enable a uwsgi configuration that runs under uwsgi."""
    if uwsgi_is_enabled(config_name):
        return

    # uwsgi is started/stopped using init script. We don't know if it can
    # handle some configuration already running against newly enabled
    # configuration. So, stop first before enabling new configuration.
    service_stop('uwsgi')

    enabled_path = UWSGI_ENABLED_PATH.format(config_name=config_name)
    available_path = UWSGI_AVAILABLE_PATH.format(config_name=config_name)
    os.symlink(available_path, enabled_path)

    service_enable('uwsgi')
    service_start('uwsgi')


def uwsgi_disable(config_name):
    """Disable a uwsgi configuration that runs under uwsgi."""
    if not uwsgi_is_enabled(config_name):
        return

    # If uwsgi is restarted later, it won't stop the just disabled
    # configuration due to how init scripts are written for uwsgi.
    service_stop('uwsgi')
    enabled_path = UWSGI_ENABLED_PATH.format(config_name=config_name)
    os.unlink(enabled_path)
    service_start('uwsgi')


def get_addresses() -> list[dict[str, str | bool]]:
    """Return a list of IP addresses and hostnames."""
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


def get_ip_addresses() -> list[dict[str, str | bool]]:
    """Return a list of IP addresses assigned to the system."""
    addresses = []

    output = subprocess.check_output(['ip', '-o', 'addr'])
    for line in output.decode().splitlines():
        parts = line.split()
        address: dict[str, str | bool] = {
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
        override_data += override_template.format(package=package, key=key,
                                                  value=value)

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as override_file:
        override_file.write(override_data)

    env = os.environ.copy()
    env['DEBCONF_DB_OVERRIDE'] = 'File{' + override_file.name + \
                                 ' readonly:true}'
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    subprocess.run(['dpkg-reconfigure', package], env=env, check=False)

    try:
        os.remove(override_file.name)
    except OSError:
        pass


def debconf_set_selections(presets):
    """Answer debconf questions before installing a package."""
    try:
        # Workaround Debian Bug #487300. In some situations, debconf complains
        # it can't find the question being answered even though it is supposed
        # to create a dummy question for it.
        subprocess.run(['/usr/share/debconf/fix_db.pl'], check=True)
    except (FileNotFoundError, PermissionError):
        pass

    presets = '\n'.join(presets)
    subprocess.check_output(['debconf-set-selections'], input=presets.encode())


def is_disk_image():
    """Return whether the current machine is from a disk image.

    Two primary ways to install FreedomBox are:
    - Using FreedomBox image for various hardware platforms.
    - Installing packages on a Debian machine using apt.
    """
    return os.path.exists('/var/lib/freedombox/is-freedombox-disk-image')


def run_apt_command(arguments):
    """Run apt-get with provided arguments."""
    command = ['apt-get', '--assume-yes', '--quiet=2'] + arguments

    env = os.environ.copy()
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    process = subprocess.run(command, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, env=env, check=False)
    return process.returncode


@contextmanager
def apt_hold(packages):
    """Prevent packages from being removed during apt operations.

    `apt-mark hold PACKAGES` accepts a list of packages. But if one of
    the package is missing from the apt repository, then it will fail
    to hold any of the listed packages. So it is necessary to try to
    hold each package by itself.

    Packages held by this context will be unheld when leaving the
    context. But if a package was already held beforehand, it will be
    ignored (and not unheld).

    """
    held_packages = []
    for package in packages:
        current_hold = subprocess.check_output(
            ['apt-mark', 'showhold', package])
        if not current_hold:
            process = subprocess.run(['apt-mark', 'hold', package],
                                     check=False)
            if process.returncode == 0:  # success
                held_packages.append(package)

    yield held_packages

    for package in held_packages:
        subprocess.check_call(['apt-mark', 'unhold', package])


@contextmanager
def apt_hold_freedombox():
    """Prevent freedombox package from being removed during apt operations."""
    current_hold = subprocess.check_output(
        ['apt-mark', 'showhold', 'freedombox'])
    try:
        if current_hold:
            # Package is already held, possibly by administrator.
            yield current_hold
        else:
            # Set the flag.
            apt_hold_flag.touch(mode=0o660)
            yield subprocess.check_call(['apt-mark', 'hold', 'freedombox'])
    finally:
        # Was the package held, either in this process or a previous one?
        if not current_hold or apt_hold_flag.exists():
            apt_unhold_freedombox()


def apt_unhold_freedombox():
    """Remove any hold on freedombox package, and clear flag."""
    subprocess.run(['apt-mark', 'unhold', 'freedombox'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   check=False)
    if apt_hold_flag.exists():
        apt_hold_flag.unlink()


def is_package_manager_busy():
    """Return whether package manager is busy.
    This command uses the `lsof` command to check whether the dpkg lock file
    is open which indicates that the package manager is busy"""
    LOCK_FILE = '/var/lib/dpkg/lock'
    try:
        subprocess.check_output(['lsof', LOCK_FILE])
        return True
    except subprocess.CalledProcessError:
        return False


def podman_create(container_name: str, image_name: str, volume_name: str,
                  volume_path: str, volumes: dict[str, str] | None = None,
                  env: dict[str, str] | None = None):
    """Remove and recreate a podman container."""
    service_stop(f'{volume_name}-volume.service')
    service_stop(container_name)

    directory = pathlib.Path('/etc/containers/systemd')
    directory.mkdir(parents=True, exist_ok=True)

    subprocess.run(['podman', 'volume', 'rm', '--force', volume_name],
                   check=False)

    directory = pathlib.Path('/etc/containers/systemd')
    directory.mkdir(parents=True, exist_ok=True)

    pathlib.Path(volume_path).mkdir(parents=True, exist_ok=True)
    # Create storage volume
    volume_file = directory / f'{volume_name}.volume'
    contents = f'''[Volume]
Device={volume_path}
Driver=local
VolumeName={volume_name}
Options=bind
'''
    volume_file.write_text(contents)

    service_file = directory / f'{container_name}.container'
    volume_lines = '\n'.join([
        f'Volume={source}:{dest}' for source, dest in (volumes or {}).items()
    ])
    env_lines = '\n'.join(
        [f'Environment={key}={value}' for key, value in (env or {}).items()])
    contents = f'''[Unit]
Requires=nextcloud-freedombox-volume.service
After=nextcloud-freedombox-volume.service

[Container]
AutoUpdate=registry
ContainerName=%N
{env_lines}
Image={image_name}
Network=host
{volume_lines}

[Service]
Restart=always

[Install]
WantedBy=default.target
'''
    service_file.write_text(contents)
    service_daemon_reload()


def podman_uninstall(container_name: str, volume_name: str, image_name: str,
                     volume_path: str):
    """Remove a podman container's components and systemd unit."""
    subprocess.run(['podman', 'volume', 'rm', '--force', volume_name],
                   check=True)
    subprocess.run(['podman', 'image', 'rm', '--ignore', image_name],
                   check=True)
    volume_file = pathlib.Path(
        '/etc/containers/systemd/') / f'{volume_name}.volume'
    volume_file.unlink(missing_ok=True)
    service_file = pathlib.Path(
        '/etc/containers/systemd/') / f'{container_name}.container'
    service_file.unlink(missing_ok=True)
    shutil.rmtree(volume_path, ignore_errors=True)
    service_daemon_reload()
