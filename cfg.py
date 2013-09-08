from menu import Menu
import os

from ConfigParser import SafeConfigParser
parser = SafeConfigParser(
    defaults={
        'root':os.path.dirname(os.path.realpath(__file__)),
        'product_name':"",
        'box_name':"",
        'file_root':"",
        'python_root':"",
        'data_dir':"",
        'store_file':"",
        'user_db':"",
        'status_log_file':"",
        'access_log_file':"",
        'users_dir':"",
        'host':"127.0.0.1",
        'pidfile':"",
        'port':"",
        })
parser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plinth.config'))

product_name = parser.get('Name', 'product_name')
box_name = parser.get('Name', 'box_name')
root = parser.get('Path', 'root')
file_root = parser.get('Path', 'file_root')
python_root = parser.get('Path', 'python_root')
data_dir = parser.get('Path', 'data_dir')
store_file = parser.get('Path', 'store_file')
user_db = parser.get('Path', 'user_db')
status_log_file = parser.get('Path', 'status_log_file')
access_log_file = parser.get('Path', 'access_log_file')
users_dir = parser.get('Path', 'users_dir')
pidfile = parser.get('Path', 'pidfile')
host = parser.get('Network', 'host')
port = int(parser.get('Network', 'port'))

html_root = None
main_menu = Menu()
base_href = ""

if store_file.endswith(".sqlite3"):
    store_file = os.path.splitext(store_file)[0]
