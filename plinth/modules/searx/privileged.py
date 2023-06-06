# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure searx."""

import gzip
import os
import pathlib
import secrets
import shutil

import augeas
import yaml

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.searx.manifest import PUBLIC_ACCESS_SETTING_FILE
from plinth.utils import gunzip

SETTINGS_FILE = '/etc/searx/settings.yml'

UWSGI_FILE = '/etc/uwsgi/apps-available/searx.ini'


def _copy_uwsgi_configuration():
    """Copy example uwsgi configuration

    Copy the example uwsgi configuration shipped with Searx documentation to
    the appropriate uwsgi directory.
    """
    example_config = ('/usr/share/doc/searx/examples/'
                      'uwsgi/apps-available/searx.ini')
    if not os.path.exists(UWSGI_FILE):
        shutil.copy(example_config, os.path.dirname(UWSGI_FILE))


def _update_uwsgi_configuration():
    """Fix uwsgi configuration.

    uwsgi 2.0.15-debian crashes when trying to autoload.
    """
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/inifile/lens', 'Puppet.lns')
    aug.set('/augeas/load/inifile/incl[last() + 1]', UWSGI_FILE)
    aug.load()
    aug.set('/files/etc/uwsgi/apps-available/searx.ini/uwsgi/autoload',
            'false')
    aug.set('/files/etc/uwsgi/apps-available/searx.ini/uwsgi/chmod-socket',
            '660')
    aug.save()


def _generate_secret_key(settings):
    """Generate a secret key for the Searx installation."""
    secret_key = secrets.token_hex(64)
    settings['server']['secret_key'] = secret_key


def _set_title(settings):
    """Set the page title to '{box_name} Web Search'."""
    title = 'FreedomBox Web Search'
    settings['general']['instance_name'] = title


def _set_timeout(settings):
    """Set timeout to 20 seconds."""
    settings['outgoing']['request_timeout'] = 20.0


def _set_safe_search(settings):
    """Set safe search to Moderate."""
    settings['search']['safe_search'] = 1


@privileged
def set_safe_search(filter_: int):
    """Set safe search filter for search results."""
    settings = read_settings()
    settings['search']['safe_search'] = filter_
    write_settings(settings)


@privileged
def get_safe_search() -> int:
    """Return the value of the safe search setting."""
    if os.path.exists(SETTINGS_FILE):
        settings = read_settings()
        return int(settings['search']['safe_search'])
    else:
        return 0


def read_settings():
    """Load settings as dictionary from YAML config file."""
    with open(SETTINGS_FILE, 'rb') as settings_file:
        return yaml.safe_load(settings_file)


def write_settings(settings):
    """Write settings from dictionary to YAML config file."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as settings_file:
        yaml.dump(settings, settings_file)


def _get_example_settings_file():
    searx_doc_dir = pathlib.Path('/usr/share/doc/searx/examples/')
    if (searx_doc_dir / 'settings.yml').exists():
        return searx_doc_dir / 'settings.yml'

    return searx_doc_dir / 'settings.yml.gz'


def _update_search_engines(settings):
    """Update settings with the latest supported search engines."""
    example_settings_file = _get_example_settings_file()
    open_func = gzip.open if example_settings_file.suffix == '.gz' else open
    with open_func(example_settings_file, 'rb') as example_settings:
        settings['engines'] = yaml.safe_load(example_settings)['engines']


@privileged
def setup():
    """Post installation actions for Searx."""
    _copy_uwsgi_configuration()
    _update_uwsgi_configuration()

    if not os.path.exists(SETTINGS_FILE):
        example_settings_file = _get_example_settings_file()
        if example_settings_file.suffix == '.gz':
            gunzip(str(example_settings_file), SETTINGS_FILE)
        else:
            pathlib.Path(SETTINGS_FILE).parent.mkdir(mode=0o755)
            shutil.copy(example_settings_file, SETTINGS_FILE)

    settings = read_settings()
    _generate_secret_key(settings)
    _set_title(settings)
    _set_timeout(settings)
    _set_safe_search(settings)
    _update_search_engines(settings)
    write_settings(settings)

    action_utils.service_restart('uwsgi')


@privileged
def enable_public_access():
    """Enable public access to the SearX application."""
    open(PUBLIC_ACCESS_SETTING_FILE, 'w', encoding='utf-8').close()


@privileged
def disable_public_access():
    """Disable public access to the SearX application."""
    if os.path.exists(PUBLIC_ACCESS_SETTING_FILE):
        os.remove(PUBLIC_ACCESS_SETTING_FILE)


@privileged
def uninstall():
    """Remove configuration uWSGI file."""
    shutil.rmtree('/etc/searx', ignore_errors=True)
    pathlib.Path(UWSGI_FILE).unlink(missing_ok=True)
