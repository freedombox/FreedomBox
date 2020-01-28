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

import logging
import threading

from plinth import dbus, network
from plinth.utils import import_from_gi

glib = import_from_gi('GLib', '2.0')

_thread = None
_main_loop = None

logger = logging.getLogger(__name__)


def run():
    """Run a glib main loop forever in a thread."""
    global _thread
    _thread = threading.Thread(target=_run)
    _thread.start()


def stop():
    """Exit glib main loop and end the thread."""
    if _main_loop:
        logger.info('Exiting glib main loop')
        _main_loop.quit()


def _run():
    """Connect to D-Bus and run main loop."""
    logger.info('Started new thread for glib main loop.')

    # Initialize all modules that use glib main loop
    dbus.init()
    network.init()

    global _main_loop
    _main_loop = glib.MainLoop()
    _main_loop.run()
    _main_loop = None

    logger.info('Glib main loop thread exited.')
