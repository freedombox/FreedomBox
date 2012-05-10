"""The HTTPS Santiago listener and sender."""

from simplesantiago import SantiagoListener, SantiagoSender

import cherrypy
import httplib, urllib
import sys


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

        try:
            self.incoming_request(kwargs["request"])
        except:
            pass

    @cherrypy.expose
    def query(self, host, service):
        """Request a resource from another Santiago client.

        TODO: add request whitelisting.

        """
        if not cherrypy.request.remote.ip.startswith("127.0.0"):
            return

        self.santiago.query(host, service)

    @cherrypy.expose
    def save_server(self):
        if not cherrypy.request.remote.ip.startswith("127.0.0"):
            return

        self.santiago.save_server()

class Sender(SantiagoSender):

    def __init__(self, santiago, proxy_host, proxy_port):

        super(SantiagoSender, self).__init__(santiago)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def outgoing_request(self, request, destination):
        """Send an HTTPS request to each Santiago client.

        Don't queue, just immediately send the reply to each location we know.

        It's both simple and as reliable as possible.

        """
        params = urllib.urlencode(request)

        # TODO: Does HTTPSConnection require the cert and key?
        # Is the fact that the server has it sufficient?  I think so.
        connection = httplib.HTTPSConnection(destination.split("//")[1])

        # proxying required and available only in Python 2.7 or later.
        # TODO: fail if Python version < 2.7.
        if sys.version_info >= (2, 7):
            connection.set_tunnel(self.proxy_host, self.proxy_port)

        connection.request("GET", "/?%s" % params)
        connection.close()
