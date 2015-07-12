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

import configparser
import os

from plinth.menu import Menu

product_name = None
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
pidfile = None
host = None
port = None
use_x_forwarded_host = False
secure_proxy_ssl_header = None
debug = False
no_daemon = False
server_dir = '/'

main_menu = Menu()

CONFIG_FILE = None
DEFAULT_CONFIG_FILE = '/etc/plinth/plinth.config'
DEFAULT_ROOT = '/'


def read():
    """Read configuration"""
    global CONFIG_FILE  # pylint: disable-msg=W0603
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        CONFIG_FILE = DEFAULT_CONFIG_FILE
        directory = DEFAULT_ROOT
    else:
        directory = os.path.dirname(os.path.realpath(__file__))
        directory = os.path.join(directory, '..')
        CONFIG_FILE = os.path.join(directory, 'plinth.config')
        if not os.path.isfile(CONFIG_FILE):
            raise FileNotFoundError('No plinth.config file could be found.')

    parser = configparser.ConfigParser(
        defaults={
            'root': os.path.realpath(directory),
        })
    parser.read(CONFIG_FILE)

    config_items = {('Name', 'product_name'),
                    ('Name', 'box_name'),
                    ('Path', 'root'),
                    ('Path', 'file_root'),
                    ('Path', 'config_dir'),
                    ('Path', 'data_dir'),
                    ('Path', 'store_file'),
                    ('Path', 'actions_dir'),
                    ('Path', 'doc_dir'),
                    ('Path', 'status_log_file'),
                    ('Path', 'access_log_file'),
                    ('Path', 'pidfile'),
                    ('Path', 'server_dir'),
                    ('Network', 'host'),
                    ('Network', 'port'),
                    ('Network', 'secure_proxy_ssl_header'),
                    ('Network', 'use_x_forwarded_host')}

    for section, name in config_items:
        try:
            value = parser.get(section, name)
            globals()[name] = value
        except (configparser.NoSectionError, configparser.NoOptionError):
            print('Configuration does not contain the {}.{} option.'
                  .format(section, name))
            raise

    global port  # pylint: disable-msg=W0603
    port = int(port)
