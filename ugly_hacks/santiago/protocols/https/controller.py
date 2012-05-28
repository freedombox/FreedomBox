"""The HTTPS Santiago listener and sender.

"""


from santiago import SantiagoListener, SantiagoSender

import cherrypy
import httplib, urllib, urlparse
import sys
import logging


def setup(santiago):
    # TODO call this bugger to prep the dispatcher, objects, etc.
    pass

class Listener(SantiagoListener):

    def __init__(self, santiago, socket_port=0,
                 ssl_certificate="", ssl_private_key=""):

        super(SantiagoListener, self).__init__(santiago)

        cherrypy.server.socket_port = socket_port
        cherrypy.server.ssl_certificate = ssl_certificate
        cherrypy.server.ssl_private_key = ssl_private_key
        cherrypy.Application(self, "/")

    def start(self):
        """Starts the listener."""

        # TODO: integrate multiple servers:
        # http://docs.cherrypy.org/dev/refman/process/servers.html
        # cherrypy.engine.start()
        cherrypy.quickstart(self)

    @cherrypy.expose
    def index(self, **kwargs):
        """Receive an incoming Santiago request from another Santiago client."""

        logging.debug("protocols.https.index: Received request {0}".format(str(kwargs)))
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
            logging.debug("protocols.https.query: Request from non-local IP")
            return

        return super(Listener, self).learn(host, service)

    @cherrypy.expose
    def where(self, host, service):
        """Show where a host is providing me services.

        TODO: make the output format a parameter.

        """
        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            logging.debug("protocols.https.query: Request from non-local IP")
            return

        return list(super(Listener, self).where(host, service))

    @cherrypy.expose
    def provide(self, client, service, location):
        """Provide a service for the client at the location."""

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            logging.debug("protocols.https.query: Request from non-local IP")
            return

        return super(Listener, self).provide(client, service, location)

    @cherrypy.expose
    def pdb(self):
        """Set a trace."""

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            logging.debug("protocols.https.query: Request from non-local IP")
            return

        import pdb; pdb.set_trace()

class Sender(SantiagoSender):

    def __init__(self, santiago, proxy_host, proxy_port):

        super(SantiagoSender, self).__init__(santiago)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def outgoing_request(self, request, destination):
        """Send an HTTPS request to each Santiago client.

        Don't queue, just immediately send the reply to each location we know.

        It's both simple and as reliable as possible.

        ``request`` is literally the request's text.  It needs to be wrapped for
        transport across the protocol.

        """
        logging.debug("protocols.https.Sender.outgoing_request: request {0}".format(str(request)))
        to_send = { "request": request }

        params = urllib.urlencode(to_send)
        logging.debug("protocols.https.Sender.outgoing_request: params {0}".format(str(params)))

        # TODO: Does HTTPSConnection require the cert and key?
        # Is the fact that the server has it sufficient?  I think so.
        connection = httplib.HTTPSConnection(destination.split("//")[1])

        # proxying required and available only in Python 2.7 or later.
        # TODO: fail if Python version < 2.7.
        if sys.version_info >= (2, 7):
            connection.set_tunnel(self.proxy_host, self.proxy_port)

        connection.request("GET", "/?%s" % params)
        connection.close()
