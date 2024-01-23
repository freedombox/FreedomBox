# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Module to handle glib main loop and provide asynchronous utilities.
"""

import logging
import random
import threading

from plinth import dbus, network
from plinth.utils import import_from_gi

from . import cfg

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


def schedule(interval, method, data=None, in_thread=True, repeat=True,
             add_jitter=True):
    """Schedule a recurring call to a method with fixed interval."""

    def _runner():
        """Run the target method and log and exceptions."""
        try:
            return method(data)
        except Exception as exception:  # pylint: disable=broad-except
            logger.exception('Exception in running scheduled method - %s',
                             exception)

    def _run_bare_or_thread(_user_data):
        """Run the target method in thread or directly (if async)."""
        if not in_thread:
            _runner()
            return repeat

        thread = threading.Thread(target=_runner)
        thread.start()
        return repeat

    # When running in development mode, reduce the interval for tasks so that
    # they are triggered quickly and frequently to facilitate debugging.
    if cfg.develop and interval > 180:
        interval = 180

    if add_jitter:
        # Add or subtract 5% random jitter to given interval to avoid many
        # tasks running at exactly the same time (and competing for DB, disk,
        # network, etc.).
        interval *= 0.95 + (random.random() * 0.1)

    glib.timeout_add(int(interval * 1000), _run_bare_or_thread, None)
