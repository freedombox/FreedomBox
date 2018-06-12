#
# This file is part of FreedomBox.
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

import configparser
import logging
import os

logger = logging.getLogger(__name__)

box_name = None
root = None
file_root = None
config_dir = None
data_dir = None
store_file = None
actions_dir = None
doc_dir = None
status_log_file = None
access_log_file = None
host = None
port = None
use_x_forwarded_host = False
secure_proxy_ssl_header = None
debug = False
server_dir = '/'
danube_edition = False

config_file = None

DEFAULT_CONFIG_FILE = '/etc/plinth/plinth.config'
DEFAULT_ROOT = '/'


def read(file_path=None, root_directory=None):
    """
    Read configuration.

    - file_path: path of plinth.config file
    - root_directory: path of plinth root folder
    """
    if not file_path and not root_directory:
        root_directory = DEFAULT_ROOT
        file_path = DEFAULT_CONFIG_FILE

    if not os.path.isfile(file_path):
        raise FileNotFoundError('No plinth.config file could be found.')

    global config_file  # pylint: disable-msg=invalid-name,global-statement
    config_file = file_path

    parser = configparser.ConfigParser(
        defaults={
            'root': os.path.realpath(root_directory),
        })
    parser.read(config_file)

    config_items = (
        ('Path', 'root', 'string'),
        ('Path', 'file_root', 'string'),
        ('Path', 'config_dir', 'string'),
        ('Path', 'data_dir', 'string'),
        ('Path', 'store_file', 'string'),
        ('Path', 'actions_dir', 'string'),
        ('Path', 'doc_dir', 'string'),
        ('Path', 'status_log_file', 'string'),
        ('Path', 'access_log_file', 'string'),
        ('Path', 'server_dir', 'string'),
        ('Network', 'host', 'string'),
        ('Network', 'port', 'int'),
        ('Network', 'secure_proxy_ssl_header', 'string'),
        ('Network', 'use_x_forwarded_host', 'bool'),
        ('Misc', 'box_name', 'string'),
        ('Misc', 'danube_edition', 'bool'),
    )

    for section, name, datatype in config_items:
        try:
            value = parser.get(section, name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.error('Configuration does not contain option: %s.%s',
                         section, name)
            raise
        else:
            if datatype == 'int':
                value = int(value)
            elif datatype == 'bool':
                value = (value.lower() == 'true')

            globals()[name] = value
