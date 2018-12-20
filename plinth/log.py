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
            'default': {
                'format':
                    '%(name)-14s %(levelname)-8s %(message)s',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
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
