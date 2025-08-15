# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure MediaWiki."""

import os
import pathlib
import shutil
import subprocess
import tempfile

from plinth import action_utils
from plinth.actions import privileged, secret_str
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
        process = action_utils.run(['dpkg', '-s', 'php'],
                                   stdout=subprocess.PIPE, check=True)
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
    action_utils.run(['chmod', '-R', 'o-rwx', data_dir], check=True)
    action_utils.run(['chown', '-R', 'www-data:www-data', data_dir],
                     check=True)

    conf_file = pathlib.Path(CONF_FILE)
    if not conf_file.exists():
        conf_file.write_text('<?php\n')

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
def change_password(username: str, password: secret_str):
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
def set_public_registrations(should_enable: bool):
    """Enable or Disable public registrations for MediaWiki."""
    setting = "$wgGroupPermissions['*']['createaccount']"
    conf_value = 'true' if should_enable else 'false'
    _update_setting(setting, f'{setting} = {conf_value};\n')


@privileged
def set_private_mode(should_enable: bool):
    """Enable or Disable Private mode for wiki."""
    setting = "$wgGroupPermissions['*']['read']"
    conf_value = 'false' if should_enable else 'true'
    _update_setting(setting, f'{setting} = {conf_value};\n')


@privileged
def set_default_skin(skin: str):
    """Set a default skin."""
    _update_setting('$wgDefaultSkin', f'$wgDefaultSkin = "{skin}";\n')


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
    # /etc/mediawiki is removed on purge of mediawiki package
