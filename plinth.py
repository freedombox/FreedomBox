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
Daemonizer(cherrypy.engine).subscribe()

import module_loader
import plugin_mount
import service

from logger import Logger

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011-2013, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"


def parse_arguments():
   parser = argparse.ArgumentParser(description='Plinth web interface for the FreedomBox.')
   parser.add_argument('--pidfile',
                       help='specify a file in which the server may write its pid')
   # FIXME make this work with basehref for static files.
   parser.add_argument('--server_dir',
                       help='specify where to host the server.')
   parser.add_argument("--debug", action="store_true",
                       help="Debug flag.  Don't use.")

   args=parser.parse_args()
   set_config(args, "pidfile", "plinth.pid")
   set_config(args, "server_dir", "/")
   set_config(args, "debug", False)

   return cfg

def set_config(args, element, default):
   """Sets *cfg* elements based on *args* values, or uses a reasonable default.

   - If values are passed in from *args*, use those.
   - If values are read from the config file, use those.
   - If no values have been given, use default.

   """
   try:
      # cfg.(element) = args.(element)
      setattr(cfg, element, getattr(args, element))
   except AttributeError:
      # if it fails, we didn't receive that argument.
      try:
         # if not cfg.(element): cfg.(element) = default
         if not getattr(cfg, element):
            setattr(cfg, element, default)
      except AttributeError:
         # it wasn't in the config file, but set the default anyway.
         setattr(cfg, element, default)


def setup_logging():
    """Setup logging framework"""
    cfg.log = Logger()


def setup_configuration():
   cfg = parse_arguments()

   try:
      if cfg.pidfile:
         from cherrypy.process.plugins import PIDFile
         PIDFile(cherrypy.engine, cfg.pidfile).subscribe()
   except AttributeError:
      pass

   os.chdir(cfg.python_root)


def setup_server():
    """Setup CherryPy server"""
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
        DEBUG=False,
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
    setup_logging()

    service.init()

    setup_configuration()

    configure_django()

    module_loader.load_modules()

    cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]

    setup_server()

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
