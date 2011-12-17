from menu import Menu
import os

file_root = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(file_root, "data")
base_href=""
store_file = os.path.join(data_dir, "store.sqlite3")
user_db = os.path.join(data_dir, "users")
status_log_file = os.path.join(data_dir, "status.log")
access_log_file =  os.path.join(data_dir, "access.log")
users_dir = os.path.join(data_dir, "users")

product_name = "Plinth"
box_name = "Freedom Plug"

port = 8000

## Do not edit below this line ##
html_root = None
main_menu = Menu()

