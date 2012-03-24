#! /usr/bin/python -*- mode: auto-fill; fill-column: 80; -*-

"""A simple Santiago service.

I'm tired of overanalyzing this, so I'll write something simple and work from
there.

FIXME: add that whole pgp thing.

"""

import cherrypy
import gnupg
import httplib, urllib


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

        """
        self.senders = senders
        self.hosting = hosting
        self.consuming = consuming

        self._create_listeners(listeners)
        self.me = me

    def _create_listeners(self, listeners):
        """Iterates through each known protocol creating listeners for all.

        Unfortunately, I won't be able to do this for real because this implies
        a control flow inversion, treating servers as clients to my meta-server,
        and most servers aren't built to tolerate that very well (or I don't
        know how to handle it).  I'll work on it though.

        """
        for protocol in listeners.iterkeys():
            method =  "_create_%s_listener" % protocol

            try:
                getattr(self, method)(**listeners[protocol])
            except KeyError:
                continue

    def _create_https_listener(self, port=1):
        """Registers an HTTPS listener.

        TODO: complete.  that cherrypy daemon thing.

        """
        self.socket_port = port
        index.exposed = True

    def am_i(self, server):
        return self.me == server

    def learn_service(self, client, service, locations):
        """Learn a service somebody else hosts for me."""

        self.hosting[client][santiago].update(set(locations))

    def get_locations(self, client, service):
        """Return where I'm hosting the service for the client.

        Return nothing if the client or service are unrecognized.

        """
        try:
            return self.hosting[client][service]
        except KeyError:
            pass

    def index(self, **kwargs):
        """Process an incoming Santiago request.

        This tag doesn't do any real processing, it just catches and hides
        errors from the sender, so that every request is met with silence.

        The only data an attacker should be able to pull from a client is:

        - The fact that a server exists and is serving HTTP 200s.
        - The round-trip time for that response.
        - Whether the server is up or down.

        Worst case scenario, a client causes the Python interpreter to segfault
        and the Santiago process comes down, so the system starts rejecting
        connections by default.

        """
        # no matter what happens, the sender will never hear about it.
        try:
            request = unpack_request(kwargs)

            handle_request(request["from"], request["to"],
                           request["client"], request["host"],
                           request["service"], request["reply_to"])
        except Exception:
            pass

    def unpack_request(self, kwargs):
        """Decrypt and verify the request.

        Give up if it doesn't pass muster.

        TODO: complete.

        """
        return kwargs

    def handle_request(self, from_, to, client, host, service, reply_to):
        """Actually do the request processing.

        #. Verify we're willing to host for both the client and proxy.  If we
           aren't, quit and return nothing.

        #. Forward the request if it's not for me.

        #. Learn new Santiagi if they were sent.

        #. Reply to the client.

        """
        try:
            self.hosting[from_]
            self.hosting[client]
        except KeyError:
            return

        if not self.am_i(to):
            self.proxy()

        if reply_to is not None:
            self.learn_service(client, "santiago", reply_to)

        self.reply(client, self.get_hosting_locations(client, service), service,
                   self.get_serving_locations(client, service))

    def proxy(self):
        """Pass off a request to another Santiago.

        TODO: complete.

        """
        pass

    def reply(self, client, location, service, reply_to):
        """Send the reply to each Santiago client.

        Don't queue, just immediately send the reply to each location we know.

        It's both simple and as reliable as possible.

        """
        params = urllib.urlencode({ "request": pgp.signencrypt(
            {"from": self.me, "to": client,
             "host": self.me, "client": client,
             "service": service, "locations": location,
             "reply_to": self.get_hosting_locations(client, "santiago")})})

        for reply in reply_to:
            connection = httplib.HTTPSConnection(reply)
            connection.request("POST", "", params)
            connection.close()

if __name__ == "__main__":
    port = 8090

    listeners = { "https": { "port": port } }
    senders = ({ "protocol": "http",
                 "proxy": "localhost:4030" },)

    hosting = { "a": { "santiago": set( "localhost:%s" % port )}}
    consuming = { "santiagao": { "a": set( "localhost:4030" )}}

    cherrypy.quickstart(SimpleSantiago(listeners, senders,
                                       hosting, consuming, "b"),
                        '/')
