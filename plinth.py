#!/usr/bin/env python

import os, sys, argparse
import cfg
import django.conf
import django.core.wsgi
if not os.path.join(cfg.file_root, "vendor") in sys.path:
   sys.path.append(os.path.join(cfg.file_root, "vendor"))

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer

import module_loader
import plugin_mount
import service

import logger
from logger import Logger

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011-2013, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Plinth web interface for FreedomBox')
    parser.add_argument(
        '--pidfile', default='plinth.pid',
        help='specify a file in which the server may write its pid')
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
    cfg.log = Logger()


def setup_server():
    """Setup CherryPy server"""
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
    cherrypy.tree.mount(None, cfg.server_dir + '/static', config)

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
        'username': request.session.get(cfg.session_key, None),
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

    template_directories = module_loader.get_template_directories()
    sessions_directory = os.path.join(cfg.data_dir, 'sessions')
    django.conf.settings.configure(
        DEBUG=cfg.debug,
        ALLOWED_HOSTS=['127.0.0.1', 'localhost'],
        TEMPLATE_DIRS=template_directories,
        INSTALLED_APPS=['bootstrapform'],
        ROOT_URLCONF='urls',
        SESSION_ENGINE='django.contrib.sessions.backends.file',
        SESSION_FILE_PATH=sessions_directory,
        STATIC_URL=cfg.server_dir + '/static/',
        TEMPLATE_CONTEXT_PROCESSORS=context_processors)


def main():
    """Intialize and start the application"""
    parse_arguments()

    setup_logging()
    logger.init()

    service.init()

    os.chdir(cfg.python_root)

    configure_django()

    module_loader.load_modules()

    cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]

    setup_server()

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
