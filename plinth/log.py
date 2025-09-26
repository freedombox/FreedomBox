# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Setup logging for the application.
"""

import logging
import logging.config
import typing
import warnings

from . import cfg

default_level = None


class LogEmitterProtocol(typing.Protocol):
    unit: str


class LogEmitter:
    """A mixin for App components that emit logs.

    Used as a simple base class for identifying components that have logs. Use
    the self.unit property to fetch systemd journal logs of the unit.
    """

    unit: str

    def get_logs(self: LogEmitterProtocol) -> dict[str, str]:
        from plinth.privileged import service as service_privileged
        return service_privileged.get_logs(self.unit)


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


def _capture_warnings():
    """Capture all warnings include deprecation warnings."""
    # Capture all Python warnings such as deprecation warnings
    logging.captureWarnings(True)

    # Log all deprecation warnings when in develop mode
    if cfg.develop:
        warnings.filterwarnings('default', '', DeprecationWarning)
        warnings.filterwarnings('default', '', PendingDeprecationWarning)
        warnings.filterwarnings('default', '', ImportWarning)


def action_init():
    """Initialize logging for action scripts."""
    _capture_warnings()

    configuration = get_configuration()
    # Don't log to console
    configuration['root']['handlers'] = ['journal']
    logging.config.dictConfig(configuration)


def init():
    """Setup the logging framework."""
    import cherrypy

    # Remove default handlers and let the log message propagate to root logger.
    for cherrypy_logger in [cherrypy.log.error_log, cherrypy.log.access_log]:
        for handler in list(cherrypy_logger.handlers):
            cherrypy_logger.removeHandler(handler)

    _capture_warnings()


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
            },
            'journal': {
                'class': 'systemd.journal.JournalHandler'
            }
        },
        'root': {
            'handlers': ['console', 'journal'],
            'level': default_level or ('DEBUG' if cfg.develop else 'INFO')
        },
        'loggers': {
            'django.db.backends': {
                'level': 'INFO'  # Set to 'DEBUG' to log database queries
            },
            'axes': {
                'level': 'INFO'  # Too verbose during DEBUG
            }
        }
    }

    return configuration
