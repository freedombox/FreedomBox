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
import logging
import re
import shelve
import sys

import pgpprocessor
import utilities


class Santiago(object):
    """This Santiago is a less extensible Santiago.

    The client and server are unified, and it has hardcoded support for
    protocols.

    """
    SUPPORTED_PROTOCOLS = set([1])
    ALL_KEYS = set(("host", "client", "service", "locations", "reply_to",
                    "request_version", "reply_versions"))
    REQUIRED_KEYS = set(("client", "host", "service",
                         "request_version", "reply_versions"))
    OPTIONAL_KEYS = ALL_KEYS ^ REQUIRED_KEYS
    LIST_KEYS = set(("reply_to", "locations", "reply_versions"))

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
        self.requests = DefaultDict(set)
        self.me = me
        self.gpg = gnupg.GPG(use_agent = True)

        if listeners:
            self.listeners = self._create_connectors(listeners, "Listener")
        if senders:
            self.senders = self._create_connectors(senders, "Sender")

        self.shelf = shelve.open(str(self.me))
        self.hosting = hosting if hosting else self.load_data("hosting")
        self.consuming = consuming if consuming else self.load_data("consuming")

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

        FIXME: Assumes the current directory is in sys.path

        """
        import_name = "protocols." + protocol

        if not import_name in sys.modules:
            __import__(import_name)

        return sys.modules[import_name]

    def __enter__(self):
        """Start all listeners and senders attached to this Santiago.

        When this has finished, the Santiago will be ready to go.

        """
        for connector in (list(self.listeners.itervalues()) +
                          list(self.senders.itervalues())):
            connector.start()

        logging.debug("Santiago started!")

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up and save all data to shut down the service."""

        santiago.save_data("hosting")
        santiago.save_data("consuming")
        logging.debug([key for key in santiago.shelf])

        santiago.shelf.close()

    def i_am(self, server):
        """Verify whether this server is the specified server."""

        return self.me == server

    def learn_service(self, host, service, locations):
        """Learn a service somebody else hosts for me."""
        if service not in self.consuming:
            self.consuming[service] = dict()

        if host not in self.consuming[service]:
            self.consuming[service][host] = set()

        if locations:
            self.consuming[service][host] = (
                self.consuming[service][host] | locations)

    def provide_service(self, client, service, locations):
        """Start hosting a service for somebody else."""

        if client not in self.hosting:
            self.hosting[client] = dict()

        if service not in self.hosting[client]:
            self.hosting[client][service] = set()

        if locations:
            self.hosting[client][service] = (
                self.hosting[client][service] | locations)

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
            self.outgoing_request(
                host, self.me, host, self.me,
                service, None, self.get_client_locations(host, "santiago"))
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
            str({ "host": host, "client": client,
                  "service": service, "locations": list(locations or ""),
                  "reply_to": list(reply_to),
                  "request_version": 1,
                  "reply_versions": list(Santiago.SUPPORTED_PROTOCOLS),}),
            host,
            sign=self.me)

        # FIXME use urlparse.urlparse instead!
        for destination in self.get_client_locations(host, "santiago"):
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
            logging.debug("santiago.Santiago.incoming_request: request: {0}".format(str(request)))

            unpacked = self.unpack_request(request)

            if not unpacked:
                logging.debug("santiago.Santiago.incoming_request: opaque request.")
                return

            logging.debug("santiago.Santiago.incoming_request: unpacked {0}".format(str(unpacked)))

            if unpacked["locations"]:
                logging.debug("santiago.Santiago.incoming_request: handling reply")

                self.handle_reply(
                    unpacked["from"], unpacked["to"],
                    unpacked["host"], unpacked["client"],
                    unpacked["service"], unpacked["locations"],
                    unpacked["reply_to"],
                    unpacked["request_version"],
                    unpacked["reply_versions"])
            else:
                logging.debug("santiago.Santiago.incoming_request: handling request")

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
            logging.debug(
                "santiago.Santiago.unpack_request: fail request {0}".format(
                    str(request)))
            logging.debug(
                "santiago.Santiago.unpack_request: fail fingerprint {0}".format(
                    str(request.fingerprint)))
            return

        # copy out only required keys from request, throwing away cruft
        request_body = dict()
        source = ast.literal_eval(str(request))
        try:
            for key in Santiago.ALL_KEYS:
                request_body[key] = source[key]
        except KeyError:
            logging.debug(
                "santiago.Santiago.unpack_request: missing key {0}".format(
                    str(source)))
            return

        # required keys are non-null
        if None in [request_body[x] for x in Santiago.REQUIRED_KEYS]:
            logging.debug(
                "santiago.Santiago.unpack_request: blank key {0}: {1}".format(
                    key, str(request_body)))
            return

        # move lists to sets
        request_body = self.setify_lists(request_body)
        if not request_body:
            logging.debug(
                "santiago.Santiago.unpack_request: not sets {0}".format(
                    str(request_body)))
            return

        # versions must overlap.
        if not (Santiago.SUPPORTED_PROTOCOLS & request_body["reply_versions"]):
            return
        if not (Santiago.SUPPORTED_PROTOCOLS &
              set([request_body["request_version"]])):
            return

        # set implied keys
        request_body["from"] = request.fingerprint
        request_body["to"] = self.me

        return request_body

    def setify_lists(self, request_body):
        """Convert list nodes to sets."""

        try:
            for key in Santiago.LIST_KEYS:
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
        # give up if we won't host the service for the client.
        try:
            self.hosting[client][service]
        except KeyError:
            logging.debug(
                "santiago.Santiago.handle_request: no host for you".format(
                    self.hosting))
            return

        # if we don't proxy, learn new reply locations and send the request.
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
                     service, locations, reply_to,
                     request_version, reply_versions):
        """Process a reply from a Santiago service.

        The last call in the chain that makes up the Santiago system, we now
        take the reply from the other Santiago server and learn any new service
        locations, if we've requested locations for that service.

        """
        logging.debug("santiago.Santiago.handle_reply: local {0}".format(str(locals())))

        # give up if we won't consume the service from the proxy or the client.
        try:
            if service not in self.requests[host]:
                logging.debug(
                    "santiago.Santiago.handle_reply: unrequested service {0}: ".format(
                        service, self.requests))
                return
        except KeyError:
            logging.debug(
                "santiago.Santiago.handle_reply: unrequested host {0}: ".format(
                    host, self.requests))
            return

        # give up or proxy if the message isn't for me.
        if not self.i_am(to):
            logging.debug(
                "santiago.Santiago.handle_reply: not to {0}".format(to))
            return
        if not self.i_am(client):
            logging.debug(
                "santiago.Santiago.handle_reply: not client {0}".format(client))
            self.proxy()
            return

        self.learn_service(host, "santiago", reply_to)
        self.learn_service(host, service, locations)

        self.requests[host].remove(service)
        # clean buffers
        # TODO clean up after 5 minutes to allow all hosts to reply?
        if not self.requests[host]:
            del self.requests[host]

        logging.debug("santiago.Santiago.handle_reply: Success!")
        logging.debug("santiago.Santiago.handle_reply: consuming {0}".format(
                self.consuming))
        logging.debug("santiago.Santiago.handle_reply: requests {0}".format(
                self.requests))

    def load_data(self, key):
        """Load hosting or consuming data from the shelf.

        To do this correctly, we need to convert the list values to sets.
        However, that can be done only after unwrapping the signed data.

        pre::

            key in ("hosting", "consuming")

        post::

            getattr(self, key) # exists

        """
        logging.debug("santiago.Santiago.load_data: loading data.")

        if not key in ("hosting", "consuming"):
            logging.debug(
                "santiago.Santiago.load_data: bad key {0}".format(key))
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
                data = dict(ast.literal_eval(str(message)))
            except (ValueError, SyntaxError) as e:
                logging.exception(e)
                data = dict()

        logging.debug("santiago.Santiago.load_data: found {0}: {1}".format(
                key, data))

        data = Santiago.convert_data(data, set)

        return data

    def save_data(self, key):
        """Save hosting and consuming data to file.

        To do this safely, we'll need to convert the set subnodes to lists.
        That way, we'll be able to sign the data correctly.

        pre::

            key in ("hosting", "consuming")

        """
        logging.debug("santiago.Santiago.save_data: saving data.")

        if not key in ("hosting", "consuming"):
            logging.debug(
                "santiago.Santiago.save_data: bad key {0}".format(key))
            return

        data = getattr(self, key)

        data = Santiago.convert_data(data, list)

        logging.debug(
            "santiago.Santiago.save_data: saving {0}: {1}".format(key, data))

        data = str(self.gpg.encrypt(str(data), recipients=[self.me],
                                    sign=self.me))

        self.shelf[key] = data

        logging.debug(
            "santiago.Santiago.save_data: saved {0}: {1}".format(key, data))

    @classmethod
    def convert_data(cls, data, acallable):
        """Convert the data in the sub-dictionary by calling callable on it.

        For example, to convert a hosts dictionary with a list in it to a host
        dictonary made of sets, use:

        >>> adict = { "alice": { "santiago": list([1, 2]) }}
        >>> Santiago.convert_data(adict, set)
        { "alice": { "santiago": set([1, 2]) }}

        """
        for first in data.iterkeys():
            for second in data[first].iterkeys():
                data[first][second] = acallable(data[first][second])

        logging.debug("santiago.Santiago.convert_data: data {0}".format(data))
        return data

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

        TODO: add request whitelisting.

        """
        return self.santiago.query(host, service)

    def provide(self, client, service, location):
        """Provide a service for the client at the location."""

        return self.santiago.provide_service(client, service, set([location]))

class SantiagoSender(SantiagoConnector):
    """Generic Santiago Sender superclass.

    This class contains one required method, the request sending method.  This
    method sends a Santiago request via that protocol.

    """
    def outgoing_request(self):
        raise Exception(
            "santiago.SantiagoSender.outgoing_request not implemented.")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    cert = "santiago.crt"
    mykey = utilities.load_config("production.cfg").get("pgpprocessor", "keyid")

    listeners = { "https": { "socket_port": 8080,
                             "ssl_certificate": cert,
                             "ssl_private_key": cert }, }
    senders = { "https": { "proxy_host": "localhost",
                           "proxy_port": 8118} }
    hosting = { mykey: { "santiago": set( ["https://localhost:8080"] )}}
    consuming = { "santiago": { mykey: set( ["https://localhost:8080"] )}}

    santiago = Santiago(listeners, senders,
                        hosting, consuming,
                        me=mykey)

    # import pdb; pdb.set_trace()
    with santiago:
        pass
    logging.debug("Santiago finished!")
