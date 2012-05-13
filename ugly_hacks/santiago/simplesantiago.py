#! /usr/bin/python -*- mode: python; mode: auto-fill; fill-column: 80; -*-

"""A simple Santiago service.

Start me with:

    $ python -i simplesantiago.py

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

We also don't:

- Proxy requests.
- Use a reasonable data-store.
- Have a decent control mechanism.

:FIXME: add that whole pgp thing.
:TODO: add doctests
:TODO: Create startup script that adds all necessary things to the PYTHONPATH.
:FIXME: allow multiple listeners and senders per protocol (with different
    proxies)
:TODO: move to santiago.py, merge the documentation.

This dead-drop is what came of my trying to learn from bug 4185.

"""

import ast
import cfg
from collections import defaultdict as DefaultDict
from errors import InvalidSignatureError, UnwillingHostError
import gnupg
import logging
from pgpprocessor import Unwrapper
import re
import sys


def load_data(server, item):
    """Return evaluated file contents.

    FIXME: use withsqlite instead.

    """
    with open("%s_%s" % (server, item)) as infile:
        return eval(infile.read())


class Santiago(object):
    """This Santiago is a less extensible Santiago.

    The client and server are unified, and it has hardcoded support for
    protocols.

    """
    SUPPORTED_PROTOCOLS = set([1])
    ALL_KEYS = ("host", "client", "service", "locations", "reply_to",
                "request_version", "reply_versions")
    REQUIRED_KEYS = ("client", "host", "service",
                     "request_version", "reply_versions")
    OPTIONAL_KEYS = ("locations", "reply_to")
    LIST_KEYS = ("reply_to", "locations", "reply_versions")

    def __init__(self, listeners = None, senders = None,
                 hosting = None, consuming = None, me = 0):
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
        self.hosting = hosting
        self.consuming = consuming
        self.requests = DefaultDict(set)
        self.me = me
        self.gpg = gnupg.GPG(use_agent = True)

        if listeners:
            self.listeners = self._create_connectors(listeners, "Listener")
        if senders:
            self.senders = self._create_connectors(senders, "Sender")

    def _create_connectors(self, settings, connector):
        """Iterates through each protocol given, creating connectors for all.

        This assumes that the caller correctly passes parameters for each
        connector.  If not, we log a TypeError and continue to serve any
        connectors we can create successfully.  If other types of errors occur,
        we quit.

        """
        connectors = dict()

        for protocol in settings.iterkeys():
            module = SimpleSantiago._get_protocol_module(protocol)

            try:
                connectors[protocol] = \
                    getattr(module, connector)(self, **settings[protocol])

            # log a type error, assume all others are fatal.
            except TypeError:
                logging.error("Could not create %s %s with %s",
                              protocol, connector, str(settings[protocol]))

        return connectors

    @classmethod
    def _get_protocol_module(cls, protocol):
        """Return the requested protocol module.

        FIXME: Assumes the current directory is in sys.path

        """
        import_name = "protocols." + protocol

        if not import_name in sys.modules:
            __import__(import_name)

        return sys.modules[import_name]

    def start(self):
        """Start all listeners and senders attached to this Santiago.

        When this has finished, the Santiago will be ready to go.

        """
        for connector in list(self.listeners.itervalues()) + \
                         list(self.senders.itervalues()):
            connector.start()

        logging.debug("Santiago started!")

    def i_am(self, server):
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
        except KeyError as e:
            logging.exception(e)

    def get_client_locations(self, host, service):
        """Return where the host serves the service for me, the client."""

        try:
            return self.consuming[service][host]
        except KeyError as e:
            logging.exception(e)

    def query(self, host, service):
        """Request a service from another Santiago.

        This tag starts the entire Santiago request process.

        """
        try:
            self.requests[host].add(service)

            self.outgoing_request(
                host, self.me, host, self.me,
                service, None, self.get_client_locations(host, "santiago"))
        except Exception as e:
            logging.exception("Couldn't handle %s.%s", host, service)

    def outgoing_request(self, from_, to, host, client,
                service, locations, reply_to):
        """Send a request to another Santiago service.

        This tag is used when sending queries or replies to other Santiagi.

        """
        # FIXME sign the encrypted payload.
        payload = self.gpg.encrypt(
                {"host": host, "client": client,
                 "service": service, "locations": locations or "",
                 "reply_to": reply_to}, to, sign=self.me)
        request = self.gpg.sign({"request": payload, "to": to})

        for destination in self.get_client_locations(to, "santiago"):
            protocol = destination.split(":")[0]
            self.senders[protocol].outgoing_request(request, destination)

    def incoming_request(self, request):
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
            if not verify_message(request):
                return

            unpacked = self.unpack_request(request)

            if not unpacked:
                return

            if unpacked["locations"]:
                self.handle_reply(
                    unpacked["from"], unpacked["to"],
                    unpacked["host"], unpacked["client"],
                    unpacked["service"], unpacked["locations"],
                    unpacked["reply_to"],
                    unpacked["request_version"],
                    unpacked["reply_version"])
            else:
                self.handle_request(
                    unpacked["from"], unpacked["to"],
                    unpacked["host"], unpacked["client"],
                    unpacked["service"], unpacked["reply_to"],
                    unpacked["request_version"],
                    unpacked["reply_version"])

        except Exception as e:
            logging.exception("Error: ", str(e))

    def verify_request(self, request):
        """Make sure the request meets minimum criteria before we process it.

        - The request must contain required keys.
        - The request and client must be of and support protocol versions I
          understand.

        """
        if False in map(request.__contains__,
                        ("request", "request_version", "reply_versions")):
            return False

        if not (Santiago.SUPPORTED_PROTOCOLS & set(request["reply_versions"])):
            return False

        if not (Santiago.SUPPORTED_PROTOCOLS &
              set([request["request_version"]])):
            return False

        return True

    def unpack_request(self, request):
        """Decrypt and verify the request.

        The request comes in encrypted and it's decrypted here.  If I can't
        decrypt it, it's not for me.  If it has no signature, I don't want it.

        Some lists are changed to sets here.  This allows for set-operations
        (union, intersection, etc) later, making things much more intuitive.

        """
        request = self.gpg.decrypt(request)

        # skip badly signed messages or ones for other folks.
        if not (str(request) and request.fingerprint):
            return

        # copy out only required keys from request, throwing away cruft
        request_body = dict()
        source = ast.literal_eval(str(request))
        try:
            for key in Santiago.ALL_KEYS:
                request_body[key] = source[key]
        except KeyError:
            return

        # required keys are non-null
        if None in [request_body[x] for x in Santiago.REQUIRED_KEYS]:
            return

        # move lists to sets
        request_body = self.setify_lists(request_body)
        if not request_body:
            return

        # set implied keys
        request_body["from"] = request.fingerprint
        request_body["to"] = self.me

        return request_body

    def setify_lists(self, request_body):
        """Convert list nodes to sets."""

        try:
            for key in ("locations", "reply_to"):
                if request_body[key] is not None:
                    request_body[key] = set(request_body[key])
        except TypeError:
            return

        try:
            for key in ("reply_versions",):
                request_body[key] = set(request_body[key])
        except TypeError:
            return

        return request_body


    def handle_request(self, from_, to, host, client,
                       service, reply_to, request_version, reply_versions):
        """Actually do the request processing.

        - Verify we're willing to host for both the client and proxy.  If we
          aren't, quit and return nothing.
        - Forward the request if it's not for me.
        - Learn new Santiagi if they were sent.
        - Reply to the client on the appropriate protocol.

        """
        if False in map(self.hosting.__contains__, (from_, client)):
            return

        if not self.i_am(host):
            self.proxy(to, host, client, service, reply_to)
        else:
            self.learn_service(client, "santiago", reply_to)

            self.outgoing_request(
                self.me, client, self.me, client,
                service, self.get_host_locations(client, service),
                self.get_host_locations(client, "santiago"))

    def proxy(self, request):
        """Pass off a request to another Santiago.

        Attempt to contact the other Santiago and ask it to reply both to the
        original host as well as me.

        TODO: add tests.
        TODO: create.

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
        except KeyError as e:
            return

        if not self.i_am(to):
            return

        if not self.i_am(client):
            self.proxy()
            return

        self.learn_service(host, "santiago", reply_to)

        if service in self.requests[host]:
            self.learn_service(host, service, locations)
            self.requests[host].remove(service)

    def save_server(self):
        """Save all operational data to files.

        Save all files with the ``self.me`` prefix.

        """
        for datum in ("hosting", "consuming"):
            name = "%s_%s" % (self.me, datum)

            try:
                with open(name, "w") as output:
                    output.write(str(getattr(self, datum)))
            except Exception as e:
                logging.exception("Could not save %s as %s", datum, name)

class SantiagoConnector(object):
    """Generic Santiago connector superclass.

    All types of connectors should inherit from this class.  These are the
    "controllers" in the MVC paradigm.

    """
    def __init__(self, santiago):
        self.santiago = santiago

    def start(self):
        """Called when initialization is complete.

        Cannot block.

        """
        pass

class SantiagoListener(SantiagoConnector):
    """Generic Santiago Listener superclass.

    This class contains one optional method, the request receiving method.  This
    method passes the request along to the Santiago host.

    """
    def incoming_request(self, **kwargs):
        self.santiago.incoming_request(**kwargs)

class SantiagoSender(SantiagoConnector):
    """Generic Santiago Sender superclass.

    This class contains one required method, the request sending method.  This
    method sends a Santiago request via that protocol.

    """
    def outgoing_request(self):
        raise Exception(
            "santiago.SantiagoSender.outgoing_request not implemented.")


if __name__ == "__main__":
    # FIXME: convert this to the withsqlite setup.

    cert = "santiago.crt"
    listeners = { "https": { "socket_port": 8080,
                             "ssl_certificate": cert,
                             "ssl_private_key": cert }, }
    senders = { "https": { "proxy_host": "localhost",
                           "proxy_port": 8118} }
    mykey = "D95C32042EE54FFDB25EC3489F2733F40928D23A"
    # mykey = "0928D23A" # my short key

    # load hosting
    try:
        hosting = load_data(mykey, "hosting")
    except IOError:
        hosting = { "a": { "santiago": set( ["https://localhost:8080"] )},
                    mykey: { "santiago": set( ["https://localhost:8080"] )}}
    # load consuming
    try:
        consuming = load_data(mykey, "consuming")
    except IOError:
        consuming = { "santiago": { mykey: set( ["https://localhost:8080"] ),
                                    "a": set( ["someAddress.onion"] )}}

    # load the Santiago
    santiago_b = SimpleSantiago(listeners, senders,
                                hosting, consuming, mykey)

    santiago_b.start()
