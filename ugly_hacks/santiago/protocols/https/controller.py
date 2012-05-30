"""The HTTPS Santiago listener and sender.

"""


import santiago

import cherrypy
import httplib, urllib, urlparse
import sys
import logging


def setup(santiago):
    """Module-level setup function.

    Called after listener and senders are set up, before they're started.

    # TODO call this bugger to prep the dispatcher, objects, etc.

    """
    pass

def start():
    """Module-level start function, called after listener and sender started.

    TODO: integrate multiple servers:

        http://docs.cherrypy.org/dev/refman/process/servers.html

    """
    cherrypy.engine.start()

class Listener(santiago.SantiagoListener):

    def __init__(self, my_santiago, socket_port=0,
                 ssl_certificate="", ssl_private_key=""):

        super(santiago.SantiagoListener, self).__init__(my_santiago)

        cherrypy.server.socket_port = socket_port
        cherrypy.server.ssl_certificate = ssl_certificate
        cherrypy.server.ssl_private_key = ssl_private_key
        cherrypy.tree.mount(cherrypy.Application(self, "/"))

    def start(self):
        """Starts the listener."""

        santiago.debug_log("Starting listener.")
        
        cherrypy.engine.start()

        santiago.debug_log("Listener started.")

    def stop(self):
        """Shuts down the listener."""

        santiago.debug_log("Stopping listener.")
        
        cherrypy.engine.stop()
        cherrypy.engine.exit()

        santiago.debug_log("Listener stopped.")
        

    @cherrypy.expose
    def index(self, **kwargs):
        """Receive an incoming Santiago request from another Santiago client."""

        santiago.debug_log("protocols.https.index: Received request {0}".format(str(kwargs)))
        try:
            self.incoming_request(kwargs["request"])
        except Exception as e:
            logging.exception(e)

    @cherrypy.expose
    def learn(self, host, service):
        """Request a resource from another Santiago client.

        TODO: add request whitelisting.

        """
        # TODO enforce restfulness, POST, and build a request form.
        # if not cherrypy.request.method == "POST":
        #     return

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        return super(Listener, self).learn(host, service)

    @cherrypy.expose
    def where(self, host, service):
        """Show where a host is providing me services.

        TODO: make the output format a parameter.

        """
        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        return list(super(Listener, self).where(host, service))

    @cherrypy.expose
    def provide(self, client, service, location):
        """Provide a service for the client at the location."""

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        return super(Listener, self).provide(client, service, location)

    @cherrypy.expose
    def pdb(self):
        """Set a trace."""

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        import pdb; pdb.set_trace()

class Sender(santiago.SantiagoSender):

    def __init__(self, my_santiago, proxy_host, proxy_port):

        super(santiago.SantiagoSender, self).__init__(my_santiago)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def outgoing_request(self, request, destination):
        """Send an HTTPS request to each Santiago client.

        Don't queue, just immediately send the reply to each location we know.

        It's both simple and as reliable as possible.

        ``request`` is literally the request's text.  It needs to be wrapped for
        transport across the protocol.

        """
        santiago.debug_log("request {0}".format(str(request)))
        to_send = { "request": request }

        params = urllib.urlencode(to_send)
        santiago.debug_log("params {0}".format(str(params)))

        # TODO: Does HTTPSConnection require the cert and key?
        # Is the fact that the server has it sufficient?  I think so.
        connection = httplib.HTTPSConnection(destination.split("//")[1])

        # proxying required and available only in Python 2.7 or later.
        # TODO: fail if Python version < 2.7.
        if sys.version_info >= (2, 7):
            connection.set_tunnel(self.proxy_host, self.proxy_port)

        connection.request("GET", "/?%s" % params)
        connection.close()
