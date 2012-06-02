"""The HTTPS Santiago listener and sender.

"""


import santiago

from Cheetah.Template import Template
import cherrypy
import httplib, urllib, urlparse
import sys
import logging


def start(*args, **kwargs):
    """Module-level start function, called after listener and sender started.

    """
    cherrypy.engine.start()

def stop(*args, **kwargs):
    """Module-level stop function, called after listener and sender stopped.

    """
    cherrypy.engine.stop()
    cherrypy.engine.exit()


class Listener(santiago.SantiagoListener):

    def __init__(self, my_santiago, socket_port=0,
                 ssl_certificate="", ssl_private_key=""):

        santiago.debug_log("Creating Listener.")

        super(santiago.SantiagoListener, self).__init__(my_santiago)

        cherrypy.server.socket_port = socket_port
        cherrypy.server.ssl_certificate = ssl_certificate
        cherrypy.server.ssl_private_key = ssl_private_key

        d = cherrypy.dispatch.RoutesDispatcher()
        d.connect("index", "/", self.index)
        d.connect("learn", "/learn/:host/:service", self.learn)
        d.connect("where", "/where/:host/:service", self.where)
        d.connect("provide", "/provide/:host/:service/:location", self.provide)

        cherrypy.tree.mount(cherrypy.Application(self), "",
                            {"/": {"request.dispatch": d}})

        santiago.debug_log("Listener Created.")

    def index(self, **kwargs):
        """Receive an incoming Santiago request from another Santiago client."""

        santiago.debug_log("Received request {0}".format(str(kwargs)))

        # FIXME Blammo!
        # make sure there's some verification of the incoming connection here.

        try:
            self.incoming_request(kwargs["request"])
        except Exception as e:
            logging.exception(e)

            if not cherrypy.request.remote.ip.startswith("127.0.0."):
                santiago.debug_log("Request from non-local IP")
                return

            raise cherrypy.HTTPRedirect("/freedombuddy")

    def learn(self, host, service, **kwargs):
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

    def where(self, host, service, **kwargs):
        """Show where a host is providing me services.

        TODO: make the output format a parameter.

        """
        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        return list(super(Listener, self).where(host, service))

    def provide(self, client, service, location, **kwargs):
        """Provide a service for the client at the location."""

        if not cherrypy.request.remote.ip.startswith("127.0.0."):
            santiago.debug_log("Request from non-local IP")
            return

        return super(Listener, self).provide(client, service, location)

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
        # FIXME Blammo!
        connection = httplib.HTTPSConnection(destination.split("//")[1])

        # proxying required and available only in Python 2.7 or later.
        # TODO: fail if Python version < 2.7.
        # FIXME Blammo!
        if sys.version_info >= (2, 7):
            connection.set_tunnel(self.proxy_host, self.proxy_port)

        # FIXME Blammo!
        connection.request("GET", "/?%s" % params)
        connection.close()

class Monitor(santiago.SantiagoMonitor):

    def __init__(self, aSantiago):
        santiago.debug_log("Creating Monitor.")

        super(Monitor, self).__init__(aSantiago)

        try:
            d = cherrypy.tree.apps[""].config["/"]["request.dispatch"]
        except KeyError:
            d = cherrypy.dispatch.RoutesDispatcher()

        root = Root(self.santiago)

        routing_pairs = (
            ('/hosting/:client/:service', HostedService(self.santiago)),
            ('/hosting/:client', HostedClient(self.santiago)),
            ('/hosting', Hosting(self.santiago)),
            ('/consuming/:host/:service', ConsumedService(self.santiago)),
            ('/consuming/:host', ConsumedHost(self.santiago)),
            ('/consuming', Consuming(self.santiago)),
            ("/stop", Stop(self.santiago)),
            ("/freedombuddy", root),
            )

        for location, handler in routing_pairs:
            Monitor.rest_connect(d, location, handler)

        cherrypy.tree.mount(root, "", {"/": {"request.dispatch": d}})

        santiago.debug_log("Monitor Created.")

    @classmethod
    def rest_connect(cls, dispatcher, location, controller, trailing_slash=True):
        """Simple REST connector for object/location mapping."""

        if trailing_slash:
            location = location.rstrip("/")
            location = [location, location + "/"]
        else:
            location = [location]

        for place in location:
            for a_method in ("PUT", "GET", "POST", "DELETE"):
                dispatcher.connect(controller.__class__.__name__ + a_method,
                                   place, controller=controller, action=a_method,
                                   conditions={ "method": [a_method] })

        return dispatcher

class RestMonitor(santiago.RestController):

    def __init__(self, aSantiago):
        super(RestMonitor, self).__init__()
        self.santiago = aSantiago
        self.relative_path = "protocols/https/templates/"

    def respond(self, template, values):
        return [str(Template(
                    file=self.relative_path + template,
                    searchList = [dict(values)]))]

class HostedService(RestMonitor):
    def GET(self, client, service):
        return self.respond("hostedService-get.tmpl", {
                "service": service,
                "client": client,
                "locations": self.santiago.hosting[client][service] })

class HostedClient(RestMonitor):
    def GET(self, client):
        return self.respond("hostedClient-get.tmpl",
                            { "client": client,
                              "services": self.santiago.hosting[client] })

class Hosting(RestMonitor):
    def GET(self):
        return self.respond("hosting-get.tmpl",
                            {"clients": [x for x in self.santiago.consuming]})

class ConsumedService(RestMonitor):
    def GET(self, host, service):
        return self.respond("consumedService-get.tmpl",
                            { "service": service,
                              "host": host,
                              "locations":
                                  self.santiago.consuming[host][service] })

class ConsumedHost(RestMonitor):
    def GET(self, host):
        return self.respond("consumedHost-get.tmpl",
                            { "services": self.santiago.consuming[host],
                              "host": host })

class Consuming(RestMonitor):
    def GET(self):
        return self.respond("consuming-get.tmpl",
                            { "hosts": [x for x in self.santiago.consuming]})

    def POST(self, host="", put="", delete=""):
        if put:
            self.PUT(put)
        elif delete:
            self.DELETE(delete)
        else:
            self.santiago.consuming[host] = None

        raise cherrypy.HTTPRedirect("/consuming")

    def PUT(self, put):
        self.santiago.consuming[host] = None


    def DELETE(self, delete):
        if delete in self.santiago.consuming:
            del self.santiago.consuming[delete]

class Root(RestMonitor):
    def GET(self):
        return self.respond("root-get.tmpl", {})

class Stop(RestMonitor):
    def POST(self):
        self.santiago.live = 0

    def GET(self):
        self.POST() # cause it's late and I'm tired.
