#!/usr/bin/env python

import os, sys, argparse
#import logging
from gettext import gettext as _
import cfg
if not os.path.join(cfg.file_root, "vendor") in sys.path:
   sys.path.append(os.path.join(cfg.file_root, "vendor"))

import cherrypy
from cherrypy import _cpserver
from cherrypy.process.plugins import Daemonizer
Daemonizer(cherrypy.engine).subscribe()

import plugin_mount
from util import *
from logger import Logger
#from modules.auth import AuthController, require, member_of, name_is

__version__ = "0.2.14"
__author__ = "James Vasile"
__copyright__ = "Copyright 2011, James Vasile"
__license__ = "GPLv3 or later"
__maintainer__ = "James Vasile"
__email__ = "james@jamesvasile.com"
__status__ = "Development"

def error_page(status, dynamic_msg, stock_msg):
   return page_template(template="err", title=status, main="<p>%s</p>%s" % (dynamic_msg, stock_msg))

def error_page_404(status, message, traceback, version):
   return error_page(status, message, """<p>If you believe this missing page should exist, please file a
   bug with either the Plinth project or the people responsible for
   the module you are trying to access.</p>

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

def write_cherrypy_config():
   """Write the cherrpy.config file.

   We could just make a dict instead of writing a data file and then
   reading it back, but I like the output for debugging purposes.
   Future versions might do the more efficient thing.
   """

   with open(os.path.join(cfg.file_root, "cherrypy.config"), 'w') as OUTF:
      OUTF.write(
"""### Generated file, do not edit! ###

[global]
server.socket_host = '0.0.0.0'
server.socket_port = %(port)s
server.thread_pool = 10
tools.staticdir.root = "%(fileroot)s"
tools.sessions.on = True
tools.auth.on = True
tools.sessions.storage_type = "file"
tools.sessions.timeout = 90
tools.sessions.storage_path = "%(fileroot)s/data/cherrypy_sessions"

[/static]
tools.staticdir.on = True
tools.staticdir.dir = "static"

[/favicon.ico]
tools.staticfile.on = True
tools.staticfile.filename = "%(fileroot)s/static/theme/favicon.ico"
""" % {'port':cfg.port, 'fileroot':cfg.file_root})

def parse_arguments():
   parser = argparse.ArgumentParser(description='Plinht web interface for the FreedomBox.')
   parser.add_argument('--pidfile', default="",
                       help='specify a file in which the server may write its pid')
   args=parser.parse_args()
   if args.pidfile:
      cfg.pidfile = args.pidfile

def setup():
   parse_arguments()

   try:
      if cfg.pidfile:
         from cherrypy.process.plugins import PIDFile
         PIDFile(cherrypy.engine, cfg.pidfile).subscribe()
   except AttributeError:
      pass

   os.chdir(cfg.file_root)
   cherrypy.config.update({'error_page.404': error_page_404})
   cherrypy.config.update({'error_page.500': error_page_500})
   write_cherrypy_config()
   cfg.log = Logger()
   load_modules()
   cfg.html_root = Root()
   cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]
   cfg.page_plugins = plugin_mount.PagePlugin.get_plugins()
   cfg.log("Loaded %d page plugins" % len(cfg.page_plugins))
   cfg.forms = plugin_mount.FormPlugin.get_plugins()

def main():
   setup()
   cherrypy.quickstart(cfg.html_root, script_name='/', config="cherrypy.config")



if __name__ == '__main__':
    main()
