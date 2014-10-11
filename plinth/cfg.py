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

    parser = configparser.SafeConfigParser(
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
                    ('Network', 'host'),
                    ('Network', 'port')}

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
