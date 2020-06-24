# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configuration parser and default values for configuration options.
"""

import configparser
import logging
import os
import pathlib

logger = logging.getLogger(__name__)

# [Path] section
file_root = '/usr/share/plinth'
config_dir = '/etc/plinth'
data_dir = '/var/lib/plinth'
custom_static_dir = '/var/www/plinth/custom/static'
store_file = data_dir + '/plinth.sqlite3'
actions_dir = '/usr/share/plinth/actions'
doc_dir = '/usr/share/freedombox'
server_dir = '/plinth'

# [Network] section
host = '127.0.0.1'
port = 8000

# Enable the following only if Plinth is behind a proxy server.  The
# proxy server should properly clean and the following HTTP headers:
#   X-Forwarded-For
#   X-Forwarded-Host
#   X-Forwarded-Proto
# If you enable these unnecessarily, this will lead to serious security
# problems. For more information, see
# https://docs.djangoproject.com/en/1.7/ref/settings/
#
# These are enabled by default in FreedomBox because the default
# configuration allows only connections from localhost
#
# Leave the values blank to disable
use_x_forwarded_for = True
use_x_forwarded_host = True
secure_proxy_ssl_header = 'HTTP_X_FORWARDED_PROTO'

# [Misc] section
box_name = 'FreedomBox'

# Other globals
develop = False

config_files = []


def get_develop_config_path():
    """Return config path of current source folder for development mode."""
    root_directory = os.path.dirname(os.path.realpath(__file__))
    root_directory = os.path.realpath(root_directory)
    config_path = os.path.join(root_directory, 'develop.config')
    return config_path


def get_config_path():
    """Get default config paths."""
    return '/etc/plinth/plinth.config'


def read():
    """Read all configuration files."""
    config_path = get_config_path()
    read_file(config_path)


def read_file(config_path):
    """Read and merge into defaults a single configuration file."""
    if not os.path.isfile(config_path):
        # Ignore missing configuration files
        return

    # Keep a note of configuration files read.
    config_files.append(config_path)

    parser = configparser.ConfigParser(
        defaults={
            'parent_dir':
                pathlib.Path(config_path).parent.resolve(),
            'parent_parent_dir':
                pathlib.Path(config_path).parent.parent.resolve(),
        })
    parser.read(config_path)

    config_items = (
        ('Path', 'file_root', 'string'),
        ('Path', 'config_dir', 'string'),
        ('Path', 'data_dir', 'string'),
        ('Path', 'custom_static_dir', 'string'),
        ('Path', 'store_file', 'string'),
        ('Path', 'actions_dir', 'string'),
        ('Path', 'doc_dir', 'string'),
        ('Path', 'server_dir', 'string'),
        ('Network', 'host', 'string'),
        ('Network', 'port', 'int'),
        ('Network', 'secure_proxy_ssl_header', 'string'),
        ('Network', 'use_x_forwarded_for', 'bool'),
        ('Network', 'use_x_forwarded_host', 'bool'),
        ('Misc', 'box_name', 'string'),
    )

    for section, name, datatype in config_items:
        try:
            value = parser.get(section, name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            # Use default values for any missing keys in configuration
            continue
        else:
            if datatype == 'int':
                value = int(value)
            elif datatype == 'bool':
                value = (value.lower() == 'true')

            globals()[name] = value
