# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure miscellaneous system settings."""

import os
import pathlib
import subprocess

import augeas

from plinth import action_utils
from plinth.actions import privileged

APACHE_CONF_ENABLED_DIR = '/etc/apache2/conf-enabled'
APACHE_HOMEPAGE_CONF_FILE_NAME = 'freedombox-apache-homepage.conf'
APACHE_HOMEPAGE_CONFIG = os.path.join(APACHE_CONF_ENABLED_DIR,
                                      APACHE_HOMEPAGE_CONF_FILE_NAME)

JOURNALD_FILE = pathlib.Path('/etc/systemd/journald.conf.d/50-freedombox.conf')


@privileged
def set_hostname(hostname: str):
    """Set system hostname using hostnamectl."""
    subprocess.run(
        ['hostnamectl', 'set-hostname', '--transient', '--static', hostname],
        check=True)
    action_utils.service_restart('avahi-daemon')


@privileged
def set_domainname(domainname: str | None = None):
    """Set system domainname in /etc/hosts."""
    hostname = subprocess.check_output(['hostname']).decode().strip()
    hosts_path = pathlib.Path('/etc/hosts')
    if domainname:
        insert_line = f'127.0.1.1 {hostname}.{domainname} {hostname}\n'
    else:
        insert_line = f'127.0.1.1 {hostname}\n'

    lines = hosts_path.read_text(encoding='utf-8').splitlines(keepends=True)
    new_lines = []
    found = False
    for line in lines:
        if '127.0.1.1' in line:
            new_lines.append(insert_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(insert_line)

    hosts_path.write_text(''.join(new_lines), encoding='utf-8')


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Puppet', str(JOURNALD_FILE))
    aug.set('/augeas/context', '/files' + str(JOURNALD_FILE))
    aug.load()
    return aug


def get_logging_mode() -> str:
    """Return the logging mode as none, volatile or persistent."""
    aug = load_augeas()
    storage = aug.get('Journal/Storage')
    if storage in ('volatile', 'persistent', 'none'):
        return storage

    # journald's default is 'auto'. On Debian systems, 'auto' is same
    # 'persistent' because /var/log/journal exists by default.
    return 'persistent'


@privileged
def set_logging_mode(mode: str):
    """Set the current logging mode."""
    if mode not in ('volatile', 'persistent', 'none'):
        raise ValueError('Invalid mode')

    aug = load_augeas()
    aug.set('Journal/Storage', mode)
    if mode == 'volatile':
        aug.set('Journal/MaxFileSec', '6h')
        aug.set('Journal/MaxRetentionSec', '2day')
    else:
        aug.remove('Journal/MaxFileSec')
        aug.remove('Journal/MaxRetentionSec')

    aug.remove('Journal/RuntimeMaxUse')
    JOURNALD_FILE.parent.mkdir(exist_ok=True)
    aug.save()

    # systemd-journald is socket activated, it may not be running and it does
    # not support reload.
    action_utils.service_try_restart('systemd-journald')


@privileged
def set_home_page(homepage: str):
    """Set the default app for this FreedomBox."""
    conf_file_path = os.path.join('/etc/apache2/conf-available',
                                  APACHE_HOMEPAGE_CONF_FILE_NAME)

    redirect_rule = 'RedirectMatch "^/$" "{}"\n'.format(homepage)

    with open(conf_file_path, 'w', encoding='utf-8') as conf_file:
        conf_file.write(redirect_rule)

    action_utils.webserver_enable('freedombox-apache-homepage')
