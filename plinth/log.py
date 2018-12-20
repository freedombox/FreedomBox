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
"""
Setup logging for the application.
"""

import importlib
import logging
import warnings

import cherrypy

from . import cfg


class ColoredFormatter(logging.Formatter):
    """Print parts of log message in color."""
    codes = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37,
        'bright_black': 90,
        'bright_red': 91,
        'bright_green': 92,
        'bright_yellow': 93,
        'bright_blue': 94,
        'bright_magenta': 95,
        'bright_cyan': 96,
        'bright_white': 97
    }

    level_colors = {
        'DEBUG': 'bright_black',
        'INFO': 'bright_white',
        'WARNING': 'bright_yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red'
    }

    def wrap_color(self, string, color=None):
        """Return a string wrapped in terminal escape codes for coloring."""
        if not color:
            return string

        return '\x1b[{}m'.format(self.codes[color]) + string + '\x1b[0m'

    def format(self, record):
        """Format a record into a string"""
        record_name = '{:<20}'.format(record.name)
        record.colored_name = self.wrap_color(record_name, 'bright_blue')

        level_color = self.level_colors.get(record.levelname, None)
        level_name = '{:>8}'.format(record.levelname)
        record.colored_levelname = self.wrap_color(level_name, level_color)
        return super().format(record)


def init():
    """Setup the logging framework."""
    # Remove default handlers and let the log message propagate to root logger.
    for cherrypy_logger in [cherrypy.log.error_log, cherrypy.log.access_log]:
        for handler in list(cherrypy_logger.handlers):
            cherrypy_logger.removeHandler(handler)

    # Capture all Python warnings such as deprecation warnings
    logging.captureWarnings(True)

    # Log all deprecation warnings when in develop mode
    if cfg.develop:
        warnings.filterwarnings('default', '', DeprecationWarning)
        warnings.filterwarnings('default', '', PendingDeprecationWarning)
        warnings.filterwarnings('default', '', ImportWarning)


def setup_cherrypy_static_directory(app):
    """Hush output from cherrypy static file request logging.

    Static file serving logs are hardly useful.
    """
    app.log.access_log.propagate = False
    app.log.error_log.propagate = False


def get_configuration():
    """Return the main python logging module configuration."""
    configuration = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'color': {
                '()': 'plinth.log.ColoredFormatter',
                'format': '{colored_levelname} {colored_name} {message}',
                'style': '{'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'color'
            }
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG' if cfg.develop else 'INFO'
        }
    }

    try:
        importlib.import_module('systemd.journal')
    except ModuleNotFoundError:
        pass
    else:
        configuration['handlers']['journal'] = {
            'class': 'systemd.journal.JournalHandler'
        }
        configuration['root']['handlers'].append('journal')

    return configuration
