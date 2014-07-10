#!/usr/bin/env python

import argparse
import django.conf
import django.core.management
import django.core.wsgi
import logging
import os
import stat
import sys

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer

import cfg
import module_loader
import service

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011-2013, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

LOGGER = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Plinth web interface for FreedomBox')
    parser.add_argument(
        '--pidfile', default='plinth.pid',
        help='specify a file in which the server may write its pid')
    # TODO: server_dir is actually a url prefix; use a better variable name
    parser.add_argument(
        '--server_dir', default='/',
        help='web server path under which to serve')
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='enable debugging and run server *insecurely*')
    parser.add_argument(
        '--no-daemon', action='store_true', default=False,
        help='do not start as a daemon')

    args = parser.parse_args()
    cfg.pidfile = args.pidfile
    cfg.server_dir = args.server_dir
    cfg.debug = args.debug
    cfg.no_daemon = args.no_daemon


def setup_logging():
    """Setup logging framework"""
    # Don't propagate cherrypy log messages to root logger
    logging.getLogger('cherrypy').propagate = False

    cherrypy.log.error_file = cfg.status_log_file
    cherrypy.log.access_file = cfg.access_log_file
    if not cfg.no_daemon:
        cherrypy.log.screen = False


def setup_paths():
    """Setup current directory and python import paths"""
    os.chdir(cfg.python_root)
    if not os.path.join(cfg.file_root, 'vendor') in sys.path:
        sys.path.append(os.path.join(cfg.file_root, 'vendor'))


def setup_server():
    """Setup CherryPy server"""
    LOGGER.info('Setting up CherryPy server')

    # Set the PID file path
    try:
        if cfg.pidfile:
            from cherrypy.process.plugins import PIDFile
            PIDFile(cherrypy.engine, cfg.pidfile).subscribe()
    except AttributeError:
        pass

    # Add an extra server
    server = _cpserver.Server()
    server.socket_host = '127.0.0.1'
    server.socket_port = 52854
    server.subscribe()

    # Configure default server
    cherrypy.config.update(
        {'server.socket_host': cfg.host,
         'server.socket_port': cfg.port,
         'server.thread_pool': 10})

    application = django.core.wsgi.get_wsgi_application()
    cherrypy.tree.graft(application, cfg.server_dir)

    config = {
        '/': {'tools.staticdir.root': '%s/static' % cfg.file_root,
              'tools.staticdir.on': True,
              'tools.staticdir.dir': '.'}}
    cherrypy.tree.mount(None, django.conf.settings.STATIC_URL, config)

    if not cfg.no_daemon:
        Daemonizer(cherrypy.engine).subscribe()

    cherrypy.engine.signal_handler.subscribe()


def context_processor(request):
    """Add additional context values to RequestContext for use in templates"""
    path_parts = request.path.split('/')
    active_menu_urls = ['/'.join(path_parts[:length])
                        for length in xrange(1, len(path_parts))]
    return {
        'cfg': cfg,
        'main_menu': cfg.main_menu,
        'submenu': cfg.main_menu.active_item(request),
        'request_path': request.path,
        'basehref': cfg.server_dir,
        'active_menu_urls': active_menu_urls
        }


def configure_django():
    """Setup Django configuration in the absense of .settings file"""
    context_processors = [
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.static',
        'django.core.context_processors.tz',
        'django.contrib.messages.context_processors.messages',
        'plinth.context_processor']

    logging_configuration = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format':
                '[%(asctime)s] %(name)-14s %(levelname)-8s %(message)s',
                }
            },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': cfg.status_log_file,
                'formatter': 'default'
                },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
                }
            },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if cfg.debug else 'INFO'
            }
        }

    data_file = os.path.join(cfg.data_dir, 'plinth.sqlite3')

    template_directories = module_loader.get_template_directories()
    sessions_directory = os.path.join(cfg.data_dir, 'sessions')
    django.conf.settings.configure(
        ALLOWED_HOSTS=['127.0.0.1', 'localhost'],
        CACHES={'default':
                {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
        DATABASES={'default':
                   {'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': data_file}},
        DEBUG=cfg.debug,
        INSTALLED_APPS=['bootstrapform',
                        'django.contrib.auth',
                        'django.contrib.contenttypes',
                        'django.contrib.messages'],
        LOGGING=logging_configuration,
        LOGIN_URL=cfg.server_dir + '/accounts/login/',
        LOGIN_REDIRECT_URL=cfg.server_dir + '/',
        LOGOUT_URL=cfg.server_dir + '/accounts/logout/',
        MIDDLEWARE_CLASSES = (
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'modules.first_boot.middleware.FirstBootMiddleware',
        ),
        ROOT_URLCONF='urls',
        SESSION_ENGINE='django.contrib.sessions.backends.file',
        SESSION_FILE_PATH=sessions_directory,
        STATIC_URL=os.path.join(cfg.server_dir, 'static/'),
        TEMPLATE_CONTEXT_PROCESSORS=context_processors,
        TEMPLATE_DIRS=template_directories)

    LOGGER.info('Configured Django')
    LOGGER.info('Template directories - %s', template_directories)

    if not os.path.isfile(data_file):
        LOGGER.info('Creating and initializing data file')
        django.core.management.call_command('syncdb', interactive=False)
        os.chmod(data_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)


def main():
    """Intialize and start the application"""
    parse_arguments()

    cfg.read()

    setup_logging()

    service.init()

    setup_paths()

    configure_django()

    module_loader.load_modules()

    setup_server()

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
