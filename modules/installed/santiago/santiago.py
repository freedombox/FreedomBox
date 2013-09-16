"""
santiago is the interface that listens over a tor hidden service.  It
accepts json requests and responds with json data structures filled
with information.  There is authentication involved, although I
haven't figured that one all the way through yet.
"""

import os, sys
import cherrypy
try:
    import simplejson as json
except ImportError:
    import json
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
import cfg
import util as u

santiago_port = 52854

#import gnupg

#def check_sig(query, sig):
#    "Verify that the sig and the query match"
#    gpg = gnupg.GPG(gnupghome='/home/james/')
#    return True

class Santiago(PagePlugin):
   order = 90 # order of running init in PagePlugins
   def __init__(self, *args, **kwargs):

        self.register_page("santiago")
        self.santiago_address = self.get_santiago_address() #TODO: multiple santiago ports
        #set a listener on the santiago address

   def get_santiago_address(self):
        if 'santiago' in cfg.users['admin'] and 'address' in cfg.users['admin']['santiago']:
            return cfg.users['admin']['santiago']['address']
        else:
            admin = cfg.users['admin']
            admin['santiago'] = {}

        with open ("/etc/tor/torrc", 'r') as INF:
            rc = INF.read()
        
        self.santiago_dir = os.path.join(cfg.file_root, "data", "santiago", "tor")
        self.tor_dir = os.path.join(self.santiago_dir, "general")
        u.mkdir(self.santiago_dir)
        os.system( 'chmod a+w %s' % self.santiago_dir)
        hidden_service_config = "HiddenServiceDir %s\nHiddenServicePort 80 127.0.0.1:%d" %  (self.tor_dir, santiago_port)
        if hidden_service_config in rc:
            ## get info from dir (but how? we need perms)
            ## just fake it for now
            admin['santiago']['address'] = "b5wycujkfh2jxfdo.onion"
            cfg.users['admin'] = admin
            return cfg.users['admin']['santiago']['address']
        print "Need to add these two lines to /etc/torrc:\n%s" % hidden_service_config
        return ""

   def check_for_hidden_service(self):
        pass

   @cherrypy.expose
   def index(self, *args, **kw):

        """
        A request is a dict with some required keys:
           req - this is the request.  It is a dict that has keys of use to serving the request.
           version - the version number of this description (currently 1)
           entropy - a random string of at least 256 bytes.
           signature - an optional signature
        """
        if (cherrypy.request.local.port != santiago_port
            #or not check_sig(kw['q'], kw['sig'])

            #or cherrypy.request.method.upper() != "POST"
            ):
            raise cherrypy.HTTPError(404)

        return kw['q']
        from pprint import pformat
        
        #return str(cherrypy.request.params)

        return '''
<html><head><title>CP Info</title></head>
<body><pre>%s</pre></body></html>
''' % pformat({
            'args': args,
            'kw': kw,
            'request': dict([(k, getattr(cherrypy.request, k))
                             for k in dir(cherrypy.request)
                             if not k.startswith('_')]),
        })




        #try:
          #  query = json.loads(q)
        #except:
         #   raise cherrypy.HTTPError(404)

        ## client requests proxy methods
        ## we send back a list of proxy methods (complete with routes/IP addresses to connect to)

        
        return str(cherrypy.request.local.port)
        a = "<br />".join(dir(cherrypy.request))
        a += cherrypy.request.query_string + "!!!!!!!!!!!!"
        a += str(cherrypy.request.local.port)
        return a
        return "test "  + cherrypy.request.method.upper() + " "+t

## Plinth page to config santiago
class santiago(PagePlugin):
   def __init__(self, *args, **kwargs):
      PagePlugin.__init__(self, *args, **kwargs)
      self.menu = cfg.html_root.privacy.menu.add_item("Santiago", "icon-leaf", "/privacy/santiago", 10)
      self.register_page("privacy.santiago")

   @cherrypy.expose
   @require()
   def index(self):
      return "Santiago's config goes here."
