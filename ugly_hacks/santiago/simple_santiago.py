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

:FIXME: add that whole pgp thing.
:TODO: add doctests
:TODO: Create startup script that adds all necessary things to the PYTHONPATH.
:FIXME: allow multiple listeners and senders per protocol (with different
    proxies)
:TODO: move to santiago.py, merge the documentation.

"""

import cfg
from collections import defaultdict as DefaultDict
import gnupg
import logging
import sys


def load_data(server, item):
    """Return evaluated file contents.

    FIXME: use withsqlite instead.

    """
    with open("%s_%s" % (server, item)) as infile:
        return eval(infile.read())


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
        self.hosting = hosting
        self.consuming = consuming
        self.requests = DefaultDict(set)
        self.me = me
        self.gpg = gnupg.GPG(use_agent = True)

        self.listeners = self._create_connectors(listeners, "Listener")
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
        # FIXME move it out of here so proxying can work.
        payload = self.gpg.encrypt(
                {"host": host, "client": client,
                 "service": service, "locations": locations or "",
                 "reply_to": reply_to}, to, sign=self.me)
        request = self.gpg.sign({"request": payload, "to": to})

        for destination in self.get_client_locations(to, "santiago"):
            protocol = destination.split(":")[0]
            self.senders[protocol].outgoing_request(request, destination)

    def incoming_request(self, **kwargs):
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
        logging.debug("Incoming request: ", str(kwargs))

        # no matter what happens, the sender will never hear about it.
        try:
            try:
                request = self.unpack_request(kwargs)
            except ValueError as e:
                self.proxy(kwargs)
                return

            logging.debug("Unpacked request: ", str(request))

            if request["locations"]:
                self.handle_reply(request["from"], request["to"],
                                  request["host"], request["client"],
                                  request["service"], request["locations"],
                                  request["reply_to"])
            else:
                self.handle_request(request["from"], request["to"],
                                    request["host"], request["client"],
                                    request["service"], request["reply_to"])
        except Exception as e:
            logging.exception("Error: ", str(e))

    def unpack_request(self, kwargs):
        """Decrypt and verify the request.

        Raise an (unhandled) error if there're any inconsistencies in the
        message.

        The message is wrapped in up to three ways:

        1. The outermost signature: This layer is applied to the message by the
           message's sender.  This allows for proxying signed messages between
           clients.

        2. The inner signature: This layer is applied to the message by the
           original sender (the requesting client or replying host).  The
           message's destination is recorded in plain-text in this layer so
           proxiers can deliver the message.

        3. The encrypted message: This layer is used by the host and client to
           coordinate the service, hidden from prying eyes.

        Yes, each host and client requires two verifications and one decryption
        per message.  Each proxier requires two verifications: the inner
        signature must be valid, not necessarily trusted.  The host and client
        are the only folks who must trust the inner signature.  Proxiers must
        only verify that signature.

        XXX: if we duplicate any keys in the signed message (for addressing)
             they could (should?) be overwritten by the contents of the
             encrypted message.

        TODO: Do we use "to" or "host" the plain-text inner signature?  If we
              use "host", we'll need to use "client" on the way back, but that
              feels like it gives up far too much information.

        """
        request = kwargs["request"]

        request = verify_sender(request)
        request = verify_client(request)

        if not self.am_i(request["host"]):
            self.proxy(request)
            return

        request = decrypt_client(request)

        return request

    def verify_sender(self, request):
        """Verify the signature of the message's sender.

        TODO Raises an InvalidSignature error when the signature is incorrect.

        TODO Raises an UntrustedClient error when the signer is not a client
        authorized to send us Santiago messages.

        TODO Returns the signed message's contents.

        """
        return request

    def verify_client(self, request):
        """Verify the signature of the message's source.

        TODO Raises an InvalidSignature error when the signature is incorrect.

        TODO Raises an UntrustedClient error when the signer is not a client
        authorized to send us Santiago messages.

        TODO Returns the signed message's contents.

        """
        pass

    def decrypt_client(self, request):
        """Decrypt the message and validates the encrypted signature.

        TODO Raises an InvalidSignature error when the signature is incorrect.

        TODO Raises an UntrustedClient error when the signer is not a client
        authorized to send us Santiago messages.

        TODO Returns the contents of the encrypted request.

        pre::

            self.me == request["host"]

        post::

            False not in map(("host", "client", "service", "locations",
                "reply_to"), request.__haskey__)

        """
        pass

    @staticmethod
    def signed_contents(request):
        """Return the contents of the signed message.

        TODO: complete.

        """
        if not request.readline() == "-----BEGIN PGP SIGNED MESSAGE-----":
            return

        # skip the blank line
        # contents = the thingie.
        # contents end at "-----BEGIN PGP SIGNATURE-----"
        # message ends at "-----END PGP SIGNATURE-----"

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
        except KeyError as e:
            return

        if not self.am_i(host):
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

        if not self.am_i(to):
            return

        if not self.am_i(client):
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

class SignatureError(Exception):
    pass

class InvalidSignatureError(SignatureError):
    pass

class UntrustedClientError(SignatureError):
    pass

class PgpUnwrapper(object):
    """Removes one layer of PGP message header and footer per iteration.

    Good for singly- or multiply-wrapped messages.

    FIXME: replace with a real library for this.  Why doesn't gnupg do this?

    After a single iteration, the original message is available in
    ``original_message`` while the message's contents are in
    ``str(PgpUnwrapper)``.

    Sucessive iterations unwrap additional layers of the message.  Good for
    onion-signed or -encrypted messages.

    """
    START, HEAD, BODY, FOOTER, END = "start", "header", "body", "footer", "end"

    SIG, CRYPT = "sig", "crypt"

    SIG_HEAD, SIG_BODY, SIG_FOOTER, SIG_END = (
            "-----BEGIN PGP SIGNED MESSAGE-----",
            "",
            "-----BEGIN PGP SIGNATURE-----",
            "-----END PGP SIGNATURE-----")

    CRYPT_HEAD, CRYPT_END = ("-----BEGIN PGP MESSAGE-----",
                             "-----END PGP MESSAGE-----")

    def __init__(self, message,
                 gnupg_new = None, gnupg_verify = None, gnupg_decrypt = None):

        if gnupg_new == None:
            gnupg_new = dict()
        if gnupg_verify == None:
            gnupg_verify = dict()
        if gnupg_decrypt == None:
            gnupg_decrypt = dict()

        self.message = message
        self.gnupg_new = gnupg_new
        self.gnupg_verify = gnupg_verify
        self.gnupg_decrypt = gnupg_decrypt
        self.type = ""

        self.gpg = gnupg.GPG(**self.gnupg_new)
        self.reset_fields()

    def reset_fields(self):
        """Removes all extracted data from the iterator.

        This resets it to a new or clean state, ready for the next iteration.

        """
        self.start = list()
        self.header = list()
        self.body = list()
        self.footer = list()
        self.end = list()

    def __iter__(self):
        return self

    def next(self):
        """Remove one layer of PGP message wrapping.

        Return the message's contents, and set self.body as the message's body.
        Also, set the message's header and footer in self, respectively.

        Raise an InvalidSignature Error if signature isn't valid.

        This is a really simple state-machine: certain lines advance the state
        of the machine, and until the machine is advanced again, all lines are
        added to that part of the message.  We ignore any part of the message
        that comes before the opening stanza.

        """
        point = PgpUnwrapper.START
        type_ = ""

        self.reset_fields()

        for line in self.message.splitlines():
            if point == PgpUnwrapper.START and line == PgpUnwrapper.SIG_HEAD:
                point = PgpUnwrapper.HEAD
                type_ = PgpUnwrapper.SIG
            elif point == PgpUnwrapper.START and line == PgpUnwrapper.CRYPT_HEAD:
                point = PgpUnwrapper.HEAD
                type_ = PgpUnwrapper.CRYPT
            elif point == PgpUnwrapper.HEAD and line == PgpUnwrapper.SIG_BODY:
                point = PgpUnwrapper.BODY
            elif (point == PgpUnwrapper.BODY and line == PgpUnwrapper.SIG_FOOTER and
                  type_ == PgpUnwrapper.SIG):
                point = PgpUnwrapper.FOOTER
            elif ((point == PgpUnwrapper.FOOTER and line == PgpUnwrapper.SIG_END and type_ == PgpUnwrapper.SIG) or
                  (point == PgpUnwrapper.BODY and line == PgpUnwrapper.CRYPT_END and type_ == PgpUnwrapper.CRYPT)):
                self.footer.append(line)
                point = PgpUnwrapper.END
                continue

            getattr(self, point).append(line)

        self.handle_message(point, type_)

        return "\n".join(self.body)

    def handle_message(self, point, type_):
        """Handle end-conditions of message.

        Do the right thing based on the state machine's results.

        """
        if point != PgpUnwrapper.END or type_ not in (PgpUnwrapper.CRYPT,
                                                      PgpUnwrapper.SIG):
            raise StopIteration("No valid PGP data.")

        args = (self.gnupg_verify if type_ == PgpUnwrapper.SIG
                else self.gnupg_decrypt)

        data = { PgpUnwrapper.SIG: self.gpg.verify,
                 PgpUnwrapper.CRYPT: self.gpg.decrypt}[type_](str(self), **args)

        self.body = PgpUnwrapper.unwrap(self.body)
        self.type = type_

        if not data:
            raise InvalidSignatureError()

        # reset the state machine, now that we've unwrapped a layer.
        self.message = "\n".join(self.body)

    @classmethod
    def unwrap(cls, message):
        lines = (PgpUnwrapper.SIG_HEAD, PgpUnwrapper.SIG_FOOTER,
                 PgpUnwrapper.SIG_END,
                 PgpUnwrapper.CRYPT_HEAD, PgpUnwrapper.CRYPT_END)

        for line in message:
            if True in map(str.endswith, [line] * len(lines), lines):
                message[message.index(line)] = line[2:]

        return message

    def __str__(self):
        """Returns the GPG-part of the current message.

        Non-PGP-message data are not returned.

        """
        return "\n".join([
                "\n".join(x) for x in (self.header, self.body, self.footer) ])

    def original_message(self):
        """Returns the current wrapped message.

        It's an iterator, so it discards previous iterations' data.

        """
        return "\n".join([
                "\n".join(x) for x in (self.start, self.header, self.body,
                                       self.footer, self.end) ])


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
