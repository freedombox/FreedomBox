#!/usr/bin/env python

import os, sys, argparse
from gettext import gettext as _
import cfg
if not os.path.join(cfg.file_root, "vendor") in sys.path:
   sys.path.append(os.path.join(cfg.file_root, "vendor"))

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer
Daemonizer(cherrypy.engine).subscribe()

import plugin_mount
import util as u

from logger import Logger
#from modules.auth import AuthController, require, member_of, name_is

from withsqlite.withsqlite import sqlite_db
from exmachina.exmachina import ExMachinaClient
import socket

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011-2013, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

def error_page(status, dynamic_msg, stock_msg):
   return u.page_template(template="err", title=status, main="<p>%s</p>%s" % (dynamic_msg, stock_msg))

def error_page_404(status, message, traceback, version):
   return error_page(status, message, """<p>If you believe this
   missing page should exist, please file a bug with either the Plinth
   project (<a href="https://github.com/jvasile/plinth/issues">it has
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
            raise cherrypy.InternalRedirect('/firstboot')
         elif db['state'] < 5:
            cfg.log("First Boot state = %d" % db['state'])
            raise cherrypy.InternalRedirect('/firstboot/state%d' % db['state'])
      if cherrypy.session.get(cfg.session_key, None):
         raise cherrypy.InternalRedirect('/router')
      else:
         raise cherrypy.InternalRedirect('/help/about')

def load_modules():
   """Import all the symlinked .py files in the modules directory and
   all the .py files in directories linked in the modules directory
   (but don't dive deeper than that).  Also, ignore the installed
   directory."""
   for name in os.listdir("modules"):
      if name.endswith(".py") and not name.startswith('.'):
         cfg.log.info("importing modules/%s" % name)
         try:
            __import__("modules.%s"  % (name[:-3]))
         except ImportError, e:
            cfg.log.error(_("Couldn't import modules/%s: %s") % (name, e))
      else:
         cfg.log("skipping %s" % name)

def parse_arguments():
   parser = argparse.ArgumentParser(description='Plinth web interface for the FreedomBox.')
   parser.add_argument('--pidfile', default="",
                       help='specify a file in which the server may write its pid')
   parser.add_argument('--listen-exmachina-key', default=False, action='store_true',
                       help='listen for JSON-RPC shared secret key on stdin at startup')
   args=parser.parse_args()
   if args.pidfile:
      cfg.pidfile = args.pidfile
   else:
      try:
         if not cfg.pidfile:
            cfg.pidfile = "plinth.pid"
      except AttributeError:
            cfg.pidfile = "plinth.pid"

   if args.listen_exmachina_key:
      # this is where we optionally try to read in a shared secret key to
      # authenticate connections to exmachina
      cfg.exmachina_secret_key = sys.stdin.readline().strip()
   else:
      cfg.exmachina_secret_key = None

def setup():
   parse_arguments()

   try:
      if cfg.pidfile:
         from cherrypy.process.plugins import PIDFile
         PIDFile(cherrypy.engine, cfg.pidfile).subscribe()
   except AttributeError:
      pass

   try:
      from vendor.exmachina.exmachina import ExMachinaClient
   except ImportError:
      cfg.exmachina = None
      print "unable to import exmachina client library, but continuing anyways..."
   else:
      try:
         cfg.exmachina = ExMachinaClient(
            secret_key=cfg.exmachina_secret_key or None)
      except socket.error:
         cfg.exmachina = None
         print "couldn't connect to exmachina daemon, but continuing anyways..."

   os.chdir(cfg.python_root)
   cherrypy.config.update({'error_page.404': error_page_404})
   cherrypy.config.update({'error_page.500': error_page_500})
   cfg.log = Logger()
   load_modules()
   cfg.html_root = Root()
   cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]
   cfg.page_plugins = plugin_mount.PagePlugin.get_plugins()
   cfg.log("Loaded %d page plugins" % len(cfg.page_plugins))
   cfg.forms = plugin_mount.FormPlugin.get_plugins()

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
   cherrypy.tree.mount(cfg.html_root, '/', config=config)
   cherrypy.engine.signal_handler.subscribe()


def main():
   setup()
   print "%s %d" % (cfg.host, cfg.port)

   cherrypy.engine.start()
   cherrypy.engine.block()

if __name__ == '__main__':
    main()
