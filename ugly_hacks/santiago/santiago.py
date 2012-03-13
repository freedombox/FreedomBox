#! /usr/bin/python # -*- fill-column: 80 -*-

"""The Santiago service.

It runs on a port (the Port of Santiago) with sending and receiving services
(the Santiagi) with a simple authentication mechanism ("the Dance of the
Santiagi" or "Santiago's Dance").  The idea is that systems can share
identification information without ever revealing their location (where in the
world is Santiago?).

This *is* signed identity statements, just on a service per person level.

                                  Santiago, he
                          smiles like a Buddah, 'neath
                               his red sombrero.

This file is distributed under the GNU Affero General Public License, Version 3
or later.  A copy of GPLv3 is available [from the Free Software Foundation]
<http://www.gnu.org/licenses/gpl.html>.

"""

# debug hacks
# ===========

DEBUG = 1

if DEBUG:
    """A few hacks to make testing easier."""

    def cfg_hack():
        import sys
        sys.path.append("../../")
        import cfg

    def ohnoes():
        for y in range(0, 3):
            for x in range(0, 7):
                print "WARNING",
            print ""
        print "You're in DEBUG MODE!  You are surprisingly vulnerable!  Raar!"

    ohnoes()
    cfg_hack()


# normal imports
# ==============

from collections import defaultdict as DefaultDict
import util


class Santiago(object):
    """Santiago's base class, containing listener and sender defaults."""

    def __init__(self, instance):
        """Initializes the Santiago service.

        instance is the PGP key this Santiago service is responsible for.

        Each service contains one or more senders and listeners, primarily
        divided by protocol, all pulling from and adding to the same pool of
        services.

        Each Santiago keeps track of the services it hosts, and other servers'
        Santiago services.  A Santiago has no idea of and is not responsible for
        anybody else's services.

        """
        self.instance = instance
        self.hosting = self.load_dict("hosting")
        self.keys = self.load_dict("keys")
        self.servers = self.load_dict("servers")

        self.listeners = list()
        self.senders = list()

        # load settings by name
        settings = self.load_dict("settings")
        for key in ("socket_port", "max_hops", "proxy_list"):
            setattr(self, key, settings[key] if key in settings else None)

    def load_dict(self, name):
        """Loads a dictionary from file."""

        # FIXME: figure out the threading issue.
        #return util.filedict_con("%s_%s " % (cfg.santiago, self.instance), name)
        return {
            "hosting": DefaultDict(list),
            "keys": DefaultDict(list),
            "servers": DefaultDict(lambda: DefaultDict(list)),
            "settings": DefaultDict(None)
            }[name]

    def am_i(self, server):
        """Hello?  Is it me you're looking for?"""

        return self.instance == server

    # Server-related tags
    # -------------------

    def provide_at_location(self, service, location):
        """Serve service at location.

        post::

            location in self.hosting[service]

        """
        self.hosting[service].append(location)

    def provide_for_key(self, service, key):
        """Serve service for user.

        post::

            service in self.keys[key]

        """
        self.keys[key].append(service)

    # client-related tags
    # -------------------

    def learn_service(self, service, key, locations):
        """Learn a service to use, as a client.

        post::

            forall(locations, lambda x: x in self.servers[service][key])

        """
        self.servers[service][key] += locations

    def consume_service(self, service, key):
        return self.servers[service][key]

    def add_listener(self, listener):
        """Registers a protocol-specific listener."""

        self.listeners.append(listener)

    def add_sender(self, sender):
        """Registers a sender."""

        self.senders.append(sender)

    # processing related tags
    # -----------------------

    def serve(self, key, service, server, hops, santiagi, listener):
        """Provide a requested service to a client."""

        if santiagi is not None:
            self.learn_service("santiago", key, santiagi)

        if not self.am_i(server):
            self.proxy(key, service, server, hops=hops)

        if service in self.keys[key]:
            # TODO pick the senders more intelligently.
            self.senders[0].ack(key, self.hosting[service], listener)

    def proxy(self, key, service, server, hops=3):
        """Passes a Santiago request off to another known host.

        We're trying to search the friend list for the target server.

        """
        # handle crap input.
        if (hops > self.max_hops):
            hops = self.max_hops
        if (hops < 1):
            return

        hops -= 1

        # TODO pick the senders more intelligently.
        return self.senders[0].proxy(key, service, server, hops)


class SantiagoListener(object):
    """Listens for requests on the santiago port."""

    def __init__(self, santiago, location):
        self.santiago = santiago
        self.location = location

    def serve(self, key, service, server, hops, santiagi):
        return self.santiago.serve(key, service, server, hops, santiagi, self.location)


class SantiagoSender(object):
    """Sends the Santiago request to a Santiago service."""

    def __init__(self, santiago):
        self.santiago = santiago
        self.messages = list()

    def send(self):
        """Sends all messages on the queue."""

        answer = self.messages
        self.messages = list()
        return answer

    def request(self, destination, resource):
        """Sends a request for a resource to a known Santiago.

        The request MUST include the following:

        - A service.
        - A server.

        The request MAY include the following:

        - Other Santiago listeners.
        - An action.

        post::

            not (__return__["destination"] is None)
            not (__return__["service"] is None)
            # TODO my request is signed with my GPG key, recipient encrypted.

        """
        pass # TODO: queue a request message.

    def nak(self):
        """Denies a requested resource to a Santiago.

        No reason is given.  All the recipient knows is that the host did not
        have that resource for that client.

        """
        pass

    def ack(self, key, location, listener=None):
        """A successful reply to a Santiago request.

        The response must include:

        - A server.

        The response may include:

        - The Santiago listener that received and accepted the request.

        """
        self.messages.append({
                "to": key,
                "location": location,
                "reply-to": listener,})

    def end(self):
        """Sent by the original requester, when it receives the server's
        response, telling the server it needs to send no more responses.

        Sent to the Santiago that first received the request.

        """
        pass

    def proxy(self, key, service, server, hops):
        """Sends the request to another server."""

        # TODO pull this off, another day.
        return ("%(key)s is requesting the %(service)s from %(server)s. " +
                self.santiago.instance + " is not %(server)s. " +
                "proxying request. %(hops)d hops remain.") % locals()


if __name__ == "__main__":
    import cherrypy
    import sys
    sys.path.append(".")
    from protocols.http import SantiagoHttpListener, SantiagoHttpSender

    # build the Santiago
    santiago = Santiago("nick")
    http_listener = SantiagoHttpListener(santiago)
    http_sender = SantiagoHttpSender(santiago)
    santiago.add_listener(http_listener)
    santiago.add_sender(http_sender)

    # TODO move this into the table loading.
    santiago.provide_at_location("wiki", "192.168.0.13")
    santiago.provide_for_key("wiki", "james")
    santiago.max_hops = 3
    santiago.proxy_list = ("tor")

    cherrypy.quickstart(http_listener)
