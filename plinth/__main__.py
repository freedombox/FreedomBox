#!/usr/bin/python

import argparse
import django.conf
import django.core.management
import django.core.wsgi
import importlib
import logging
import os
import stat

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer

from plinth import cfg
from plinth import module_loader
from plinth import service

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
        '/': {'tools.staticdir.root': os.path.join(cfg.file_root, 'static'),
              'tools.staticdir.on': True,
              'tools.staticdir.dir': '.'}}
    cherrypy.tree.mount(None, django.conf.settings.STATIC_URL, config)

    for module_name in module_loader.loaded_modules:
        module = importlib.import_module(module_name)
        module_path = os.path.dirname(module.__file__)
        static_dir = os.path.join(module_path, 'static')
        if not os.path.isdir(static_dir):
            continue

        config = {
            '/': {'tools.staticdir.root': static_dir,
                  'tools.staticdir.on': True,
                  'tools.staticdir.dir': '.'}}
        urlprefix = "%s%s" % (django.conf.settings.STATIC_URL, module)
        cherrypy.tree.mount(None, urlprefix, config)

    if not cfg.no_daemon:
        Daemonizer(cherrypy.engine).subscribe()

    cherrypy.engine.signal_handler.subscribe()


def configure_django():
    """Setup Django configuration in the absense of .settings file"""

    # In module_loader.py we reverse URLs for the menu before having a proper
    # request. In this case, get_script_prefix (used by reverse) returns the
    # wrong prefix. Set it here manually to have the correct prefix right away.
    django.core.urlresolvers.set_script_prefix(cfg.server_dir)

    context_processors = [
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.static',
        'django.core.context_processors.tz',
        'django.contrib.messages.context_processors.messages',
        'plinth.context_processors.common']

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

    applications = ['bootstrapform',
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                    'django.contrib.messages',
                    'plinth']
    applications += module_loader.get_modules_to_load()
    sessions_directory = os.path.join(cfg.data_dir, 'sessions')
    django.conf.settings.configure(
        ALLOWED_HOSTS=['127.0.0.1', 'localhost'],
        CACHES={'default':
                {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
        DATABASES={'default':
                   {'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': cfg.store_file}},
        DEBUG=cfg.debug,
        INSTALLED_APPS=applications,
        LOGGING=logging_configuration,
        LOGIN_URL='lib:login',
        LOGIN_REDIRECT_URL='apps:index',
        LOGOUT_URL='lib:logout',
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'plinth.modules.first_boot.middleware.FirstBootMiddleware',
        ),
        ROOT_URLCONF='plinth.urls',
        SESSION_ENGINE='django.contrib.sessions.backends.file',
        SESSION_FILE_PATH=sessions_directory,
        STATIC_URL='/'.join([cfg.server_dir, 'static/']).replace('//', '/'),
        TEMPLATE_CONTEXT_PROCESSORS=context_processors)
    django.setup()

    LOGGER.info('Configured Django with applications - %s', applications)

    LOGGER.info('Creating or adding new tables to data file')
    django.core.management.call_command('syncdb', interactive=False)
    os.chmod(cfg.store_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)


def main():
    """Intialize and start the application"""
    parse_arguments()

    cfg.read()

    setup_logging()

    service.init()

    configure_django()

    LOGGER.info('Configuration loaded from file - %s', cfg.CONFIG_FILE)

    module_loader.load_modules()

    setup_server()

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
