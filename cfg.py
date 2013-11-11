from menu import Menu
import os

import ConfigParser
from ConfigParser import SafeConfigParser

def get_item(parser, section, name):
    try:
        return parser.get(section, name)
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        print ("The config file {} does not contain the {}.{} option.".format(
                parser[0], section, name))
        raise

parser = SafeConfigParser(
    defaults={
        'root':os.path.dirname(os.path.realpath(__file__)),
        })
parser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plinth.config'))

product_name = get_item(parser, 'Name', 'product_name')
box_name = get_item(parser, 'Name', 'box_name')
root = get_item(parser, 'Path', 'root')
file_root = get_item(parser, 'Path', 'file_root')
python_root = get_item(parser, 'Path', 'python_root')
data_dir = get_item(parser, 'Path', 'data_dir')
store_file = get_item(parser, 'Path', 'store_file')
user_db = get_item(parser, 'Path', 'user_db')
status_log_file = get_item(parser, 'Path', 'status_log_file')
access_log_file = get_item(parser, 'Path', 'access_log_file')
users_dir = get_item(parser, 'Path', 'users_dir')
pidfile = get_item(parser, 'Path', 'pidfile')
host = get_item(parser, 'Network', 'host')
port = int(get_item(parser, 'Network', 'port'))

html_root = None
main_menu = Menu()
base_href = ""

if store_file.endswith(".sqlite3"):
    store_file = os.path.splitext(store_file)[0]
