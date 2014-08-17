from menu import Menu
import os

import ConfigParser
from ConfigParser import SafeConfigParser

product_name = None
box_name = None
root = None
file_root = None
python_root = None
data_dir = None
store_file = None
user_db = None
actions_dir = None
status_log_file = None
access_log_file = None
pidfile = None
host = None
port = None
debug = False
no_daemon = False
server_dir = '/'

main_menu = Menu()


def read():
    """Read configuration"""
    directory = os.path.dirname(os.path.realpath(__file__))
    parser = SafeConfigParser(
        defaults={
            'root': directory,
        })
    parser.read(os.path.join(directory, 'plinth.config'))

    config_items = {('Name', 'product_name'),
                    ('Name', 'box_name'),
                    ('Path', 'root'),
                    ('Path', 'file_root'),
                    ('Path', 'python_root'),
                    ('Path', 'data_dir'),
                    ('Path', 'store_file'),
                    ('Path', 'user_db'),
                    ('Path', 'actions_dir'),
                    ('Path', 'status_log_file'),
                    ('Path', 'access_log_file'),
                    ('Path', 'pidfile'),
                    ('Network', 'host'),
                    ('Network', 'port')}

    for section, name in config_items:
        try:
            value = parser.get(section, name)
            globals()[name] = value
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            print ('Configuration does not contain the {}.{} option.'
                   .format(section, name))
            raise

    global port  # pylint: disable-msg=W0603
    port = int(port)

    global store_file  # pylint: disable-msg=W0603
    if store_file.endswith(".sqlite3"):
        store_file = os.path.splitext(store_file)[0]

    global user_db  # pylint: disable-msg=W0603
    if user_db.endswith(".sqlite3"):
        user_db = os.path.splitext(user_db)[0]
