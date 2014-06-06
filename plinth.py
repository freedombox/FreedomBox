#!/usr/bin/env python

import os, stat, sys, argparse
from gettext import gettext as _
import cfg
import django.conf
import importlib
if not os.path.join(cfg.file_root, "vendor") in sys.path:
   sys.path.append(os.path.join(cfg.file_root, "vendor"))
import re

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer
Daemonizer(cherrypy.engine).subscribe()

import plugin_mount
import service
import util as u

from logger import Logger
#from modules.auth import AuthController, require, member_of, name_is

from withsqlite.withsqlite import sqlite_db
import socket

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011-2013, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

import urlparse

def error_page(status, dynamic_msg, stock_msg):
   return u.render_template(template="err", title=status, main="<p>%s</p>%s" % (dynamic_msg, stock_msg))

def error_page_404(status, message, traceback, version):
   return error_page(status, message, """<p>If you believe this
   missing page should exist, please file a bug with either the Plinth
   project (<a href="https://github.com/NickDaly/Plinth/issues">it has
   an issue tracker</a>) or the people responsible for the module you
   are trying to access.</p>

   <p>Sorry for the mistake.</p>
   """)

def error_page_500(status, message, traceback, version):
   cfg.log.error("500 Internal Server Error.  Trackback is above.")
   more="""<p>This is an internal error and not something you caused
   or can fix.  Please report the error on the <a
   href="https://github.com/jvasile/Plinth/issues">bug tracker</a> so
   we can fix it.</p>"""
   return error_page(status, message, "<p>%s</p><pre>%s</pre>" % (more, "\n".join(traceback.split("\n"))))

class Root(plugin_mount.PagePlugin):
   @cherrypy.expose
   def index(self):
      ## TODO: firstboot hijacking root should probably be in the firstboot module with a hook in plinth.py
      with sqlite_db(cfg.store_file, table="firstboot") as db:
         if not 'state' in db:
            # if we created a new user db, make sure it can't be read by everyone
            userdb_fname = '{}.sqlite3'.format(cfg.user_db)
            os.chmod(userdb_fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            # cherrypy.InternalRedirect throws a 301, causing the
            # browser to cache the redirect, preventing the user from
            # navigating to /plinth until the browser is restarted.
            raise cherrypy.HTTPRedirect('firstboot', 307)
         elif db['state'] < 5:
            cfg.log("First Boot state = %d" % db['state'])
            raise cherrypy.InternalRedirect('firstboot/state%d' % db['state'])
      if cherrypy.session.get(cfg.session_key, None):
         raise cherrypy.InternalRedirect('apps')
      else:
         raise cherrypy.InternalRedirect('help/about')


def load_modules():
    """
    Read names of enabled modules in modules/enabled directory and
    import them from modules directory.
    """
    for name in os.listdir('modules/enabled'):
        cfg.log.info('Importing modules/%s' % name)
        try:
            importlib.import_module('modules.{module}'.format(module=name))
        except ImportError as exception:
            cfg.log.error(
                'Could not import modules/{module}: {exception}'
                .format(module=name, exception=exception))


def get_template_directories():
    """Return the list of template directories"""
    directory = os.path.dirname(os.path.abspath(__file__))
    core_directory = os.path.join(directory, 'templates')

    directories = set((core_directory,))
    for name in os.listdir('modules/enabled'):
        directories.add(os.path.join('modules', name, 'templates'))

    cfg.log.info('Template directories - %s' % directories)

    return directories


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

def setup():
   cfg = parse_arguments()

   try:
      if cfg.pidfile:
         from cherrypy.process.plugins import PIDFile
         PIDFile(cherrypy.engine, cfg.pidfile).subscribe()
   except AttributeError:
      pass

   os.chdir(cfg.python_root)
   cherrypy.config.update({'error_page.404': error_page_404})
   cherrypy.config.update({'error_page.500': error_page_500})
   cfg.log = Logger()
   load_modules()
   cfg.html_root = Root()

   cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]
   cfg.page_plugins = plugin_mount.PagePlugin.get_plugins()
   cfg.log("Loaded %d page plugins" % len(cfg.page_plugins))

   # Add an extra server
   server = _cpserver.Server()
   server.socket_host = '127.0.0.1'
   server.socket_port = 52854
   server.subscribe()

   # Configure default server
   cherrypy.config.update(
      {'server.socket_host': cfg.host,
       'server.socket_port': cfg.port,
       'server.thread_pool':10,
       'tools.staticdir.root': cfg.file_root,
       'tools.sessions.on':True,
       'tools.auth.on':True,
       'tools.sessions.storage_type':"file",
       'tools.sessions.timeout':90,
       'tools.sessions.storage_path':"%s/cherrypy_sessions" % cfg.data_dir,})

   config = {
      '/': {'tools.staticdir.root': '%s/static' % cfg.file_root,
            'tools.proxy.on': True,},
      '/static': {'tools.staticdir.on': True,
                  'tools.staticdir.dir': "."},
      '/favicon.ico':{'tools.staticfile.on': True,
                      'tools.staticfile.filename':
                         "%s/static/theme/favicon.ico" % cfg.file_root}}
   cherrypy.tree.mount(cfg.html_root, cfg.server_dir, config=config)
   cherrypy.engine.signal_handler.subscribe()

def main():
    # Initialize basic services
    service.init()

    setup()

    # Configure Django
    template_directories = get_template_directories()
    django.conf.settings.configure(TEMPLATE_DIRS=template_directories,
                                   INSTALLED_APPS=['bootstrapform'])

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
