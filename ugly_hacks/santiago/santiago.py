#! /usr/bin/python -*- mode: python; mode: auto-fill; fill-column: 80; -*-

"""The Santiago service.

Santiago is designed to let users negotiate services without third party
interference.  By sending OpenPGP signed and encrypted messages over HTTPS (or
other protocols) between parties, I hope to reduce or even prevent MITM attacks.
Santiago can also use the Tor network as a proxy (with Python 2.7 or later),
allowing this negotiation to happen very quietly.

Start me with:

    $ python -i santiago.py

The first Santiago service queries another's index with a request.  That request
is handled and a request is returned.  Then, the reply is handled.  The upshot
is that we learn a new set of locations for the service.

We don't:

- Proxy requests.
- Use a reasonable data-store.
- Have a decent control (rate-limiting) mechanism.

:TODO: add doctests
:FIXME: allow multiple listeners and senders per protocol (with different
    proxies)

This dead-drop approach is what came of my trying to learn from bug 4185.

To see the system learn from itself, try running a few queries similar to:

#. https://localhost:8080/where/D95C32042EE54FFDB25EC3489F2733F40928D23A/santiago
#. https://localhost:8080/provide/D95C32042EE54FFDB25EC3489F2733F40928D23A/santiago/localhost:8081
#. https://localhost:8080/learn/D95C32042EE54FFDB25EC3489F2733F40928D23A/santiago
#. https://localhost:8080/where/D95C32042EE54FFDB25EC3489F2733F40928D23A/santiago

#. See what services are currently available.
#. Start serving at the "localhost:8081" location.
#. Learn the 8081 location.
#. See what services are currently available, including the 8081 service.

                                  Santiago, he
                          smiles like a Buddah, 'neath
                               his red sombrero.

This file is distributed under the GNU Affero General Public License, Version 3
or later.  A copy of GPLv3 is available [from the Free Software Foundation]
<http://www.gnu.org/licenses/gpl.html>.

"""

import ast
import cfg
from collections import defaultdict as DefaultDict
import gnupg
import inspect
import json
import logging
import re
import shelve
import sys
import time

import pgpprocessor
import utilities


def debug_log(message):
    frame = inspect.stack()
    trace = inspect.getframeinfo(frame[1][0])
    location = "{0}.{1}.{2}".format(trace.filename, trace.function,
                                    trace.lineno)
    try:
        logging.debug("{0}:{1}: {2}".format(location, time.time(), message))
    finally:
        del frame, trace, location

class Santiago(object):
    """This Santiago is a less extensible Santiago.

    The client and server are unified, and it has hardcoded support for
    protocols.

    """
    SUPPORTED_PROTOCOLS = set([1])
    # all keys must be present in the message.
    ALL_KEYS = set(("host", "client", "service", "locations", "reply_to",
                    "request_version", "reply_versions"))
    # required keys may not be null
    REQUIRED_KEYS = set(("client", "host", "service",
                         "request_version", "reply_versions"))
    # optional keys may be null.
    OPTIONAL_KEYS = ALL_KEYS ^ REQUIRED_KEYS
    LIST_KEYS = set(("reply_to", "locations", "reply_versions"))
    CONTROLLER_MODULE = "protocols.{0}.controller"

    def __init__(self, listeners = None, senders = None,
                 hosting = None, consuming = None, me = 0, monitors = None, require_gpg = 0):
        """Create a Santiago with the specified parameters.

        listeners and senders are both protocol-specific dictionaries containing
        relevant settings per protocol:

            { "http": { "port": 80 } }

        hosting and consuming are service dictionaries, one being an inversion
        of the other.  hosting contains services you host, while consuming lists
        services you use, as a client.

            hosting: { "someKey": { "someService": ( "http://a.list",
                                                     "http://of.locations" )}}

            consuming: { "someKey": { "someService": ( "http://a.list",
                                                       "http://of.locations" )}}

        Messages are delivered by defining both the source and destination
        ("from" and "to", respectively).  Separating this from the hosting and
        consuming allows users to safely proxy requests for one another, if some
        hosts are unreachable from some points.

        """
        self.live = 1
        self.requests = DefaultDict(set)
        self.me = me
        self.gpg = gnupg.GPG(use_agent = True)
        self.protocols = set()

        if listeners is not None:
            self.listeners = self.create_connectors(listeners, "Listener")
        if senders is not None:
            self.senders = self.create_connectors(senders, "Sender")
        if monitors is not None:
            self.monitors = self.create_connectors(monitors, "Monitor")

        self.shelf = shelve.open(str(self.me))
        self.hosting = hosting if hosting else self.load_data("hosting")
        self.consuming = consuming if consuming else self.load_data("consuming")

    def create_connectors(self, data, type):
        connectors = self._create_connectors(data, type)
        self.protocols |= set(connectors.keys())

        return connectors


    def _create_connectors(self, settings, connector):
        """Iterates through each protocol given, creating connectors for all.

        This assumes that the caller correctly passes parameters for each
        connector.  If not, we log a TypeError and continue to serve any
        connectors we can create successfully.  If other types of errors occur,
        we quit.

        """
        connectors = dict()

        for protocol in settings.iterkeys():
            module = Santiago._get_protocol_module(protocol)

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

        It assumes the Santiago directory is in sys.path, which seems to be a
        fair assumption.

        """
        import_name = cls.CONTROLLER_MODULE.format(protocol)

        if not import_name in sys.modules:
            __import__(import_name)

        return sys.modules[import_name]

    def __enter__(self):
        """Start all listeners and senders attached to this Santiago.

        When this has finished, the Santiago will be ready to go.

        """
        debug_log("Starting connectors.")

        for connector in (list(self.listeners.itervalues()) +
                          list(self.senders.itervalues())):
            connector.start()

        for protocol in self.protocols:
            sys.modules[Santiago.CONTROLLER_MODULE.format(protocol)].start()

        debug_log("Santiago started!")

        count = 0
        try:
            while self.live:
                time.sleep(5)
        except KeyboardInterrupt:
            pass

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up and save all data to shut down the service."""

        debug_log("Stopping Santiago.")

        for connector in (list(self.listeners.itervalues()) +
                          list(self.senders.itervalues())):
            connector.stop()

        for protocol in self.protocols:
            sys.modules[Santiago.CONTROLLER_MODULE.format(protocol)].stop()

        santiago.save_data("hosting")
        santiago.save_data("consuming")
        debug_log([key for key in santiago.shelf])

        santiago.shelf.close()

    def i_am(self, server):
        """Verify whether this server is the specified server."""

        return self.me == server

    def create_hosting_client(self, client):
        """Create a hosting client if one doesn't currently exist."""

        if client not in self.hosting:
            self.hosting[client] = dict()

    def create_hosting_service(self, client, service):
        """Create a hosting service if one doesn't currently exist.

        Check that hosting client exists before trying to add service.

        """
        self.create_hosting_client(client)

        if service not in self.hosting[client]:
            self.hosting[client][service] = list()

    def create_hosting_location(self, client, service, locations):
        """Create a hosting service if one doesn't currently exist.

        Check that hosting client exists before trying to add service.
        Check that hosting service exists before trying to add location.

        """
        self.create_hosting_service(client,service)

        for location in locations:
            if location not in self.hosting[client][service]:
                self.hosting[client][service].append(location)

    def create_consuming_host(self, host):
        """Create a consuming host if one doesn't currently exist."""

        if host not in self.consuming:
            self.consuming[host] = dict()

    def create_consuming_service(self, host, service):
        """Create a consuming service if one doesn't currently exist.

        Check that consuming host exists before trying to add service.

        """
        self.create_consuming_host(host)

        if service not in self.consuming[host]:
            self.consuming[host][service] = list()

    def create_consuming_location(self, host, service, locations):
        """Create a consuming location if one doesn't currently exist.

        Check that consuming host exists before trying to add service.
        Check that consuming service exists before trying to add location.

        """
        self.create_consuming_service(host,service)

        for location in locations:
            if location not in self.consuming[host][service]:
                self.consuming[host][service].append(location)

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
            return self.consuming[host][service]
        except KeyError as e:
            logging.exception(e)

    def query(self, host, service):
        """Request a service from another Santiago.

        This tag starts the entire Santiago request process.

        """
        try:
            self.outgoing_request(
                host, self.me, host, self.me,
                service, None, self.consuming[host]["santiago"])
        except Exception as e:
            logging.exception("Couldn't handle %s.%s", host, service)

    def outgoing_request(self, from_, to, host, client,
                         service, locations, reply_to):
        """Send a request to another Santiago service.

        This tag is used when sending queries or replies to other Santiagi.

        Each incoming item must be a single item or a list.

        The outgoing ``request`` is literally the request's text.  It needs to
        be wrapped for transport across the protocol.

        """
        self.requests[host].add(service)

        request = self.gpg.encrypt(
            json.dumps({ "host": host, "client": client,
                  "service": service, "locations": list(locations or ""),
                  "reply_to": list(reply_to),
                  "request_version": 1,
                  "reply_versions": list(Santiago.SUPPORTED_PROTOCOLS),}),
            host,
            sign=self.me)

        # FIXME use urlparse.urlparse instead!
        for destination in self.consuming[host]["santiago"]:
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
            debug_log("request: {0}".format(str(request)))

            unpacked = self.unpack_request(request)

            if not unpacked:
                debug_log("opaque request.")
                return

            debug_log("unpacked {0}".format(str(unpacked)))

            if unpacked["locations"]:
                debug_log("handling reply")

                self.handle_reply(
                    unpacked["from"], unpacked["to"],
                    unpacked["host"], unpacked["client"],
                    unpacked["service"], unpacked["locations"],
                    unpacked["reply_to"],
                    unpacked["request_version"],
                    unpacked["reply_versions"])
            else:
                debug_log("handling request")

                self.handle_request(
                    unpacked["from"], unpacked["to"],
                    unpacked["host"], unpacked["client"],
                    unpacked["service"], unpacked["reply_to"],
                    unpacked["request_version"],
                    unpacked["reply_versions"])

        except Exception as e:
            logging.exception(e)

    def unpack_request(self, request):
        """Decrypt and verify the request.

        The request comes in encrypted and it's decrypted here.  If I can't
        decrypt it, it's not for me.  If it has no signature, I don't want it.

        Some lists are changed to sets here.  This allows for set-operations
        (union, intersection, etc) later, making things much more intuitive.

        The request and client must be of and support protocol versions I
        understand.

        """
        request = self.gpg.decrypt(request)
        
        # skip badly signed messages or ones for other folks.
        if not (str(request) and request.fingerprint):
            debug_log("fail request {0}".format(str(request)))
            debug_log("fail fingerprint {0}".format(str(request.fingerprint)))
            return

        # copy out all white-listed keys from request, throwing away cruft
        request_body = dict()
        source = json.loads(str(request))
        try:
            for key in Santiago.ALL_KEYS:
                request_body[key] = source[key]
        except KeyError:
            debug_log("missing key {0}".format(str(source)))
            return

        # required keys are non-null
        if None in [request_body[x] for x in Santiago.REQUIRED_KEYS]:
            debug_log("blank key {0}: {1}".format(key, str(request_body)))
            return

        if False in [type(request_body[key]) == list for key in
                     Santiago.LIST_KEYS if request_body[key] is not None]:
            return
        
        # versions must overlap.
        if not (Santiago.SUPPORTED_PROTOCOLS &
                set(request_body["reply_versions"])):
            return
        if not (Santiago.SUPPORTED_PROTOCOLS &
              set([request_body["request_version"]])):
            return

        # set implied keys
        request_body["from"] = request.fingerprint
        request_body["to"] = self.me

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
        # give up if we won't host the service for the client.
        try:
            self.hosting[client][service]
        except KeyError:
            debug_log("no host for you".format(self.hosting))
            return

        # if we don't proxy, learn new reply locations and send the request.
        if not self.i_am(host):
            self.proxy(to, host, client, service, reply_to)
        else:
            self.create_consuming_location(client, "santiago", reply_to)

            self.outgoing_request(
                self.me, client, self.me, client,
                service, self.hosting[client][service],
                self.hosting[client]["santiago"])

    def proxy(self, request):
        """Pass off a request to another Santiago.

        Attempt to contact the other Santiago and ask it to reply both to the
        original host as well as me.

        TODO: add tests.
        TODO: create.

        """
        pass

    def handle_reply(self, from_, to, host, client,
                     service, locations, reply_to,
                     request_version, reply_versions):
        """Process a reply from a Santiago service.

        The last call in the chain that makes up the Santiago system, we now
        take the reply from the other Santiago server and learn any new service
        locations, if we've requested locations for that service.

        """
        debug_log("local {0}".format(str(locals())))

        # give up if we won't consume the service from the proxy or the client.
        try:
            if service not in self.requests[host]:
                debug_log("unrequested service {0}: ".format(
                        service, self.requests))
                return
        except KeyError:
            debug_log("unrequested host {0}: ".format(host, self.requests))
            return

        # give up or proxy if the message isn't for me.
        if not self.i_am(to):
            debug_log("not to {0}".format(to))
            return
        if not self.i_am(client):
            debug_log("not client {0}".format(client))
            self.proxy()
            return

        self.create_consuming_location(host, "santiago", reply_to)
        self.create_consuming_location(host, service, locations)

        self.requests[host].remove(service)
        # clean buffers
        # TODO clean up after 5 minutes to allow all hosts to reply?
        if not self.requests[host]:
            del self.requests[host]

        debug_log("Success!")
        debug_log("consuming {0}".format(self.consuming))
        debug_log("requests {0}".format(self.requests))

    def load_data(self, key):
        """Load hosting or consuming data from the shelf.

        To do this correctly, we need to convert the list values to sets.
        However, that can be done only after unwrapping the signed data.

        pre::

            key in ("hosting", "consuming")

        post::

            getattr(self, key) # exists

        """
        debug_log("loading data.")

        if not key in ("hosting", "consuming"):
            debug_log("bad key {0}".format(key))
            return

        try:
            data = self.shelf[key]
        except KeyError as e:
            logging.exception(e)
            data = dict()
        else:
            for message in pgpprocessor.Unwrapper(data, gpg=self.gpg):
                # iterations end when unwrapping complete.
                pass

            try:
                data = ast.literal_eval(str(message))
            except (ValueError, SyntaxError) as e:
                logging.exception(e)
                data = dict()

        debug_log("found {0}: {1}".format(key, data))

        return data

    def save_data(self, key):
        """Save hosting and consuming data to file.

        To do this safely, we'll need to convert the set subnodes to lists.
        That way, we'll be able to sign the data correctly.

        pre::

            key in ("hosting", "consuming")

        """
        debug_log("saving data.")

        if not key in ("hosting", "consuming"):
            debug_log("bad key {0}".format(key))
            return

        data = getattr(self, key)

        data = str(self.gpg.encrypt(str(data), recipients=[self.me],
                                    sign=self.me))

        self.shelf[key] = data

        debug_log("saved {0}: {1}".format(key, data))

class SantiagoConnector(object):
    """Generic Santiago connector superclass.

    All types of connectors should inherit from this class.  These are the
    "controllers" in the MVC paradigm.

    """
    def __init__(self, santiago=None, *args, **kwargs):
        super(SantiagoConnector, self).__init__(*args, **kwargs)
        self.santiago = santiago

    def setup(self):
        """Initialize the connector.

        """
        pass

    def start(self):
        """Starts the connector, called when initialization is complete.

        Cannot block.

        """
        pass

    def stop(self):
        """Shuts down the connector."""

        pass

class SantiagoListener(SantiagoConnector):
    """Generic Santiago Listener superclass.

    This class contains one optional method, the request receiving method.  This
    method passes the request along to the Santiago host.

    """
    def incoming_request(self, request):
        self.santiago.incoming_request(request)

    def where(self, host, service):
        """Return where the named host provides me a service.

        If no service is provided, return None.

        TODO: unittest

        """
        return self.santiago.get_client_locations(host, service)

    def learn(self, host, service):
        """Request a service from another Santiago client.

        """
        return self.santiago.query(host, service)

    def provide(self, client, service, location):
        """Provide a service for the client at the location."""

        return self.santiago.create_hosting_location(client, service, [location])

class SantiagoSender(SantiagoConnector):
    """Generic Santiago Sender superclass.

    This class contains one required method, the request sending method.  This
    method sends a Santiago request via that protocol.

    """
    def outgoing_request(self):
        raise Exception(
            "santiago.SantiagoSender.outgoing_request not implemented.")

class RestController(object):
    """A generic REST-style controller that reacts to the basic REST verbs."""

    def PUT(self, *args, **kwargs):
        raise NotImplemented("RestController.PUT")

    def GET(self, *args, **kwargs):
        raise NotImplemented("RestController.GET")

    def POST(self, *args, **kwargs):
        raise NotImplemented("RestController.POST")

    def DELETE(self, *args, **kwargs):
        raise NotImplemented("RestController.DELETE")

class SantiagoMonitor(RestController):
    """A REST controller that can be started and stopped."""

    def __init__(self, aSantiago):
        super(SantiagoMonitor, self).__init__()
        self.santiago = aSantiago

    def start(*args, **kwargs):
        pass

    def stop(*args, **kwargs):
        pass


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("cherrypy.error").setLevel(logging.CRITICAL)

    cert = "santiago.crt"
    mykey = utilities.load_config("production.cfg").get("pgpprocessor", "keyid")

    listeners = { "https": { "socket_port": 8080,
                             "ssl_certificate": cert,
                             "ssl_private_key": cert }, }
    senders = { "https": { "proxy_host": "localhost",
                           "proxy_port": 8118} }
    monitors = { "https": {} }

    hosting = { mykey: { "santiago": ["https://localhost:8080"] }, }
    consuming = { mykey: { "santiago": ["https://localhost:8080"] }, }

    santiago = Santiago(listeners, senders,
                        hosting, consuming,
                        me=mykey, monitors=monitors)

    # import pdb; pdb.set_trace()
    with santiago:
        pass

    debug_log("Santiago finished!")
