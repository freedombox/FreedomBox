# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure MediaWiki."""

import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import Optional

from plinth.actions import privileged
from plinth.utils import generate_password

MAINTENANCE_SCRIPTS_DIR = "/usr/share/mediawiki/maintenance"
CONF_FILE = '/etc/mediawiki/FreedomBoxSettings.php'
LOCAL_SETTINGS_CONF = '/etc/mediawiki/LocalSettings.php'


def get_php_command():
    """Return the PHP command that should be used on CLI.

    This is workaround for /usr/bin/php pointing to a different version than
    what php-defaults (and php-mbstring, php-xml) point to. See:
    https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=959742

    """
    version = ''

    try:
        process = subprocess.run(['dpkg', '-s', 'php'], stdout=subprocess.PIPE,
                                 check=True)
        for line in process.stdout.decode().splitlines():
            if line.startswith('Version:'):
                version = line.split(':')[-1].split('+')[0].strip()
    except subprocess.CalledProcessError:
        pass

    return f'php{version}'


@privileged
def setup():
    """Run the installer script to create database and configuration file."""
    data_dir = '/var/lib/mediawiki-db/'
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    if not os.path.exists(os.path.join(data_dir, 'my_wiki.sqlite')) or \
       not os.path.exists(LOCAL_SETTINGS_CONF):
        install_script = os.path.join(MAINTENANCE_SCRIPTS_DIR, 'install.php')
        password = generate_password()
        with tempfile.NamedTemporaryFile() as password_file_handle:
            password_file_handle.write(password.encode())
            password_file_handle.flush()
            subprocess.check_call([
                get_php_command(), install_script, '--confpath=/etc/mediawiki',
                '--dbtype=sqlite', '--dbpath=' + data_dir,
                '--scriptpath=/mediawiki', '--passfile',
                password_file_handle.name, 'Wiki', 'admin'
            ])
    subprocess.run(['chmod', '-R', 'o-rwx', data_dir], check=True)
    subprocess.run(['chown', '-R', 'www-data:www-data', data_dir], check=True)
    _include_custom_config()


def _include_custom_config():
    """Include FreedomBox specific configuration in LocalSettings.php."""
    with open(LOCAL_SETTINGS_CONF, 'r', encoding='utf-8') as conf_file:
        lines = conf_file.readlines()

    static_settings_index = None
    settings_index = None
    for line_number, line in enumerate(lines):
        if 'FreedomBoxSettings.php' in line:
            settings_index = line_number

        if 'FreedomBoxStaticSettings.php' in line:
            static_settings_index = line_number

    if settings_index is None:
        settings_index = len(lines)
        lines.append('include dirname(__FILE__)."/FreedomBoxSettings.php";\n')

    if static_settings_index is None:
        lines.insert(
            settings_index,
            'include dirname(__FILE__)."/FreedomBoxStaticSettings.php";\n')

    with open(LOCAL_SETTINGS_CONF, 'w', encoding='utf-8') as conf_file:
        conf_file.writelines(lines)


@privileged
def change_password(username: str, password: str):
    """Change the password for a given user."""
    change_password_script = os.path.join(MAINTENANCE_SCRIPTS_DIR,
                                          'changePassword.php')

    subprocess.check_call([
        get_php_command(), change_password_script, '--user', username,
        '--password', password
    ])


@privileged
def update():
    """Run update.php maintenance script when version upgrades happen."""
    update_script = os.path.join(MAINTENANCE_SCRIPTS_DIR, 'update.php')
    subprocess.check_call([get_php_command(), update_script, '--quick'])


@privileged
def public_registrations(command: str) -> Optional[bool]:
    """Enable or Disable public registrations for MediaWiki."""
    if command not in ('enable', 'disable', 'status'):
        raise ValueError('Invalid command')

    with open(CONF_FILE, 'r', encoding='utf-8') as conf_file:
        lines = conf_file.readlines()

    def is_pub_reg_line(line):
        return line.startswith("$wgGroupPermissions['*']['createaccount']")

    if command == 'status':
        conf_lines = list(filter(is_pub_reg_line, lines))
        return bool(conf_lines and 'true' in conf_lines[0])

    with open(CONF_FILE, 'w', encoding='utf-8') as conf_file:
        for line in lines:
            if is_pub_reg_line(line):
                words = line.split()
                if command == 'enable':
                    words[-1] = 'true;'
                else:
                    words[-1] = 'false;'
                conf_file.write(" ".join(words) + '\n')
            else:
                conf_file.write(line)

    return None


@privileged
def private_mode(command: str):
    """Enable or Disable Private mode for wiki."""
    if command not in ('enable', 'disable', 'status'):
        raise ValueError('Invalid command')

    with open(CONF_FILE, 'r', encoding='utf-8') as conf_file:
        lines = conf_file.readlines()

    def is_read_line(line):
        return line.startswith("$wgGroupPermissions['*']['read']")

    read_conf_lines = list(filter(is_read_line, lines))
    if command == 'status':
        return (read_conf_lines and 'false' in read_conf_lines[0])

    with open(CONF_FILE, 'w', encoding='utf-8') as conf_file:
        conf_value = 'false;' if command == 'enable' else 'true;'
        for line in lines:
            if is_read_line(line):
                words = line.split()
                words[-1] = conf_value
                conf_file.write(" ".join(words) + '\n')
            else:
                conf_file.write(line)

        if not read_conf_lines:
            conf_file.write("$wgGroupPermissions['*']['read'] = " +
                            conf_value + '\n')


def _update_setting(setting_name, setting_line):
    """Update the value of one setting in the config file."""
    with open(CONF_FILE, 'r', encoding='utf-8') as conf_file:
        lines = conf_file.readlines()

        inserted = False
        for i, line in enumerate(lines):
            if line.strip().startswith(setting_name):
                lines[i] = setting_line
                inserted = True
                break

        if not inserted:
            lines.append(setting_line)

    with open(CONF_FILE, 'w', encoding='utf-8') as conf_file:
        conf_file.writelines(lines)


@privileged
def set_default_skin(skin: str):
    """Set a default skin."""
    _update_setting('$wgDefaultSkin ', f'$wgDefaultSkin = "{skin}";\n')


@privileged
def set_server_url(server_url: str):
    """Set the value of $wgServer for this MediaWiki server."""
    # This is a required setting from MediaWiki 1.34
    _update_setting('$wgServer', f'$wgServer = "{server_url}";\n')


@privileged
def set_site_name(site_name: str):
    """Set the value of $wgSitename for this MediaWiki server."""
    _update_setting('$wgSitename', f'$wgSitename = "{site_name}";\n')


@privileged
def set_default_language(language: str):
    """Set the value of $wgLanguageCode for this MediaWiki server."""
    _update_setting('$wgLanguageCode ', f'$wgLanguageCode = "{language}";\n')
    # In MediaWiki 1.8 or older, if you change this after installation, you
    # should run the maintenance/rebuildmessages.php script to rebuild the
    # user interface messages (MediaWiki namespace). Otherwise, you will not
    # see the interface in the new language, or a mix of the old and new
    # languages.
    rebuild_messages_script = os.path.join(MAINTENANCE_SCRIPTS_DIR,
                                           'rebuildmessages.php')
    subprocess.check_call([get_php_command(), rebuild_messages_script])


@privileged
def uninstall():
    """Remove Mediawiki's database and local config file."""
    shutil.rmtree('/var/lib/mediawiki-db', ignore_errors=True)
    pathlib.Path(LOCAL_SETTINGS_CONF).unlink(missing_ok=True)
