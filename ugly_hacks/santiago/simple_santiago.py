#! /usr/bin/python -*- mode: python; mode: auto-fill; fill-column: 80; -*-

"""A simple Santiago service.

Start me with:

    $ python -i simple_santiago.py

This will provide you with a running Santiago service.  The important tags in
this file are:

- query
- request
- index
- handle_request
- handle_reply

They operate, essentially, in that order.  The first Santiago service queries
another's index with a request.  That request is handled and a request is
returned.  Then, the reply is handled.  The upshot is that we learn a new set of
locations for the service.

This is currently incomplete.  We don't sign, encrypt, verify, or decrypt
request messages.  I wanted to get the functional fundamentals in place first.

We also don't:

- Proxy requests.
- Use a reasonable data-store.
- Have a decent control mechanism.

FIXME: add that whole pgp thing.
FIXME: remove @cherrypy.expose from everything but index.
TODO: add doctests

"""
import cherrypy
from collections import defaultdict as DefaultDict
#import gnupg
import httplib, urllib
import sys

try:
    import cfg
except ImportError:
    # try a little harder to import cfg.  Bomb out if we still fail.
    sys.path.append("../..")
    import cfg


def load_data(server, item):
    """Return evaluated file contents.

    FIXME: use withsqlite instead.

    """
    data = ""
    with open("%s_%s" % (server, item)) as infile:
        data = eval(infile.read())
    return data


class SimpleSantiago(object):
    """This Santiago is a less extensible Santiago.

    The client and server are unified, and it has hardcoded support for
    protocols.

    """
    def __init__(self, listeners, senders, hosting, consuming, me):
        """Create a Santiago with the specified parameters.

        listeners and senders are both protocol-specific dictionaries containing
        relevant settings per protocol:

            { "http": { "port": 80 } }

        hosting and consuming are service dictionaries, one being an inversion
        of the other.  hosting contains services you host, while consuming lists
        services you use, as a client.

            hosting: { "someKey": { "someService": ( "http://a.list",
                                                     "http://of.locations" )}}

            consuming: { "someService": { "someKey": ( "http://a.list",
                                                       "http://of.locations" )}}

        Messages are delivered by defining both the source and destination
        ("from" and "to", respectively).  Separating this from the hosting and
        consuming allows users to safely proxy requests for one another, if some
        hosts are unreachable from some points.

        """
        self.senders = senders
        self.hosting = hosting
        self.consuming = consuming
        self.requests = DefaultDict(set)
        self.listeners = listeners

        self._create_listeners()
        self.me = me

    def _create_listeners(self):
        """Iterates through each known protocol creating listeners for all."""

        for protocol in self.listeners.iterkeys():
            method =  "_create_%s_listener" % protocol

            try:
                getattr(self, method)(**self.listeners[protocol])
            except KeyError:
                pass

    def _create_http_listener(self, *args, **kwargs):
        """Register an HTTP listener.

        Merely a wrapper for _create_https_listener.

        """
        self._create_https_listener(*args, **kwargs)

    def _create_https_listener(self, socket_port=0,
                               ssl_certificate="", ssl_private_key=""):
        """Registers an HTTPS listener."""

        cherrypy.server.socket_port = socket_port
        cherrypy.server.ssl_certificate = ssl_certificate
        cherrypy.server.ssl_private_key = ssl_private_key

        # reach deep into the voodoo to actually serve the index
        SimpleSantiago.index.__dict__["exposed"] = True

    def am_i(self, server):
        """Verify whether this server is the specified server."""

        return self.me == server

    def learn_service(self, host, service, locations):
        """Learn a service somebody else hosts for me."""

        if locations:
            self.consuming[service][host].union(locations)

    def provide_service(self, client, service, locations):
        """Start hosting a service for somebody else."""

        if locations:
            self.hosting[client][service].union(locations)

    def get_host_locations(self, client, service):
        """Return where I'm hosting the service for the client.

        Return nothing if the client or service are unrecognized.

        """
        try:
            return self.hosting[client][service]
        except KeyError:
            pass

    def get_client_locations(self, host, service):
        """Return where the host serves the service for me, the client."""

        try:
            return self.consuming[service][host]
        except KeyError:
            pass

    @cherrypy.expose
    def query(self, host, service):
        """Request a service from another Santiago.

        This tag starts the entire Santiago request process.

        """
        self.requests[host].add(service)

        self.request(host, self.me, host, self.me,
                     service, None, self.get_client_locations(host, "santiago"))

    def request(self, from_, to, host, client,
                service, locations, reply_to):
        """Send a request to another Santiago service.

        This tag is used when sending queries or replies to other Santiagi.

        """
        # best guess reply_to if we don't know.
        reply_to = reply_to or self.get_host_locations(to, "santiago")

        for destination in self.get_client_locations(to, "santiago"):
            getattr(self, destination.split(":")[0] + "_request") \
                (from_, to, host, client,
                 service, locations, destination, reply_to)

    def https_request(self, from_, to, host, client,
                      service, locations, destination, reply_to):
        """Send an HTTPS request to each Santiago client.

        Don't queue, just immediately send the reply to each location we know.

        It's both simple and as reliable as possible.

        TODO: pgp sign and encrypt

        """
        params = urllib.urlencode(
            {"from": from_, "to": to, "host": host, "client": client,
             "service": service, "locations": locations or "",
             "reply_to": reply_to})

        proxy = self.senders["https"]

        # TODO: Does HTTPSConnection require the cert and key?
        # Is the fact that the server has it sufficient?  I think so.
        connection = httplib.HTTPSConnection(destination.split("//")[1])

        if sys.version_info >= (2, 7):
            connection.set_tunnel(proxy["host"], proxy["port"])

        connection.request("GET", "/?%s" % params)
        connection.close()

    def index(self, **kwargs):
        """Provide a service to a client.

        This tag doesn't do any real processing, it just catches and hides
        errors from the sender, so that every request is met with silence.

        The only data an attacker should be able to pull from a client is:

        - The fact that a server exists and is serving HTTP 200s.
        - The round-trip time for that response.
        - Whether the server is up or down.

        Worst case scenario, a client causes the Python interpreter to
        segfault and the Santiago process comes down, while the system
        is set up to reject connections by default.  Then, the
        attacker knows that the last request brought down a system.

        """
        # no matter what happens, the sender will never hear about it.
        try:
            request = self.unpack_request(kwargs)

            # is this appropriate for both sending and receiving?
            # nope.
            if request["locations"]:
                self.handle_reply(request["from"], request["to"],
                                  request["host"], request["client"],
                                  request["service"], request["locations"],
                                  request["reply_to"])
            else:
                self.handle_request(request["from"], request["to"],
                                    request["host"], request["client"],
                                    request["service"], request["reply_to"])
        except Exception, e:
            #raise e
            print "Exception!", e

    def unpack_request(self, kwargs):
        """Decrypt and verify the request.

        Give up if it doesn't pass muster.

        TODO: complete.

        """
        request = DefaultDict(lambda: None)
        for k,v in kwargs.iteritems():
            request[k] = v
        return request

    def handle_request(self, from_, to, host, client,
                       service, reply_to):
        """Actually do the request processing.

        #. Verify we're willing to host for both the client and proxy.  If we
           aren't, quit and return nothing.

        #. Forward the request if it's not for me.

        #. Learn new Santiagi if they were sent.

        #. Reply to the client on the appropriate protocol.

        """
        try:
            self.hosting[from_]
            self.hosting[client]
        except KeyError:
            return

        if not self.am_i(to):
            return

        if not self.am_i(host):
            self.proxy()
        else:
            self.learn_service(client, "santiago", reply_to)

            self.request(self.me, client, self.me, client,
                         service, self.get_host_locations(client, service),
                         self.get_host_locations(client, "santiago"))

    def proxy(self):
        """Pass off a request to another Santiago.

        TODO: complete.

        """
        pass

    def handle_reply(self, from_, to, host, client,
                     service, locations, reply_to):
        """Process a reply from a Santiago service.

        The last call in the chain that makes up the Santiago system, we now
        take the reply from the other Santiago server and learn any new service
        locations, if we've requested locations for that service.

        """
        try:
            self.consuming[service][from_]
            self.consuming[service][host]
        except KeyError:
            return

        if not self.am_i(to):
            return

        if not self.am_i(client):
            self.proxy()
            return

        self.learn_service(host, "santiago", reply_to)

        if service in self.requests[host]:
            self.learn_service(host, service, locations)
            self.requests[host].remove(service)

    @cherrypy.expose
    def save_server(self):
        """Save all operational data to files.

        Save all files with the ``self.me`` prefix.

        """
        for datum in ("hosting", "consuming", "listeners", "senders"):
            name = "%s_%s" % (self.me, datum)

            try:
                with open(name, "w") as output:
                    output.write(str(getattr(self, datum)))
            except:
                pass


if __name__ == "__main__":
    # FIXME: convert this to the withsqlite setup.
    for datum in ("listeners", "senders", "hosting", "consuming"):
        locals()[datum] = load_data("b", datum)

    # Dummy Settings:
    #
    # https_port = 8090
    # cert = "/tmp/santiagoTest/santiagoTest1.crt"
    # listeners = { "https": { "socket_port": https_port,
    #                          "ssl_certificate": cert,
    #                          "ssl_private_key": cert }, }
    # senders = { "https": { "host": tor_proxy,
    #                       "port": tor_proxy_port} }
    # hosting = { "a": { "santiago": set( ["https://localhost:8090"] )},
    #             "b": { "santiago": set( ["https://localhost:8090"] )}}
    # consuming = { "santiago": { "b": set( ["https://localhost:8090"] ),
    #                             "a": set( ["someAddress.onion"] )}}

    santiago_b = SimpleSantiago(listeners, senders,
                                hosting, consuming, "b")

    # TODO: integrate multiple servers:
    # http://docs.cherrypy.org/dev/refman/process/servers.html

    # cherrypy.Application(
    cherrypy.quickstart(
        santiago_b, '/')
    # cherrypy.engine.start()
