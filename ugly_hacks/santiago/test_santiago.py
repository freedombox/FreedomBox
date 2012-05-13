#! /usr/bin/python  -*- mode: auto-fill; fill-column: 80 -*-


"""Making Santiago dance, in 4 parts:

- Validating the initial request (playing B).
- Validating the initial response (playing A).
  - Validating the silent response.
  - Validating the rejection response.
  - Validating the acceptance response.
  - Validating the forwarded request (playing C).
- Validating the forwarded request (playing D, when C isn't the target).
- Validating the forwarded response.
  - Validating the direct response (playing A).
  - Validating the indirect response (playing C, B, and A).

FIXME: Can't use the current CPy setup.  It never returns, so I can't test
against it.

If I produce a listener that just echoes the parameters, I can validate the response:

    import httplib, urllib

    params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    conn = httplib.HTTPConnection("bugs.python.org")
    print params, headers, conn

    conn.request("POST", "", params, headers)
    response = conn.getresponse()
    print response.status, response.reason

    data = response.read()
    print data

    conn.close()


"""

import os
import sys
import unittest

import gnupg
import logging
import simplesantiago as santiago
import utilities


# class SantiagoTest(unittest.TestCase):
#     """The base class for tests."""
#
#     def setUp(self):
#         super(TestServing, self).setUp()
#
#         port_a = "localhost:9000"
#         port_b = "localhost:8000"
#
#         listeners_a = [santiago.SantiagoListener(port_a)]
#         senders_a = [santiago.SantiagoSender()]
#         listeners_b = [santiago.SantiagoListener(port_b)]
#         senders_b = [santiago.SantiagoSender()]
#
#         hosting_a = { "b": { "santiago": [ port_a ]}}
#         consuming_a = { "santiagao": { "b": [ port_b ]}}
#
#         hosting_b = { "a": { "santiago": [ port_b ],
#                              "wiki": [ "localhost:8001" ]}}
#         consuming_b = { "santiagao": { "a": [ port_a ]}}
#
#         self.santiago_a = Santiago(listeners_a, senders_a, hosting_a, consuming_a)
#         self.santiago_b = Santiago(listeners_b, senders_b, hosting_b, consuming_b)
#
#     def serveOnPort(self, port):
#         """Start listening for connections on a named port.
#
#         Used in testing as a mock listener for responses from a Santiago server.
#
#         """
#         class RequestReceiver(object):
#             """A very basic listener.
#
#             It merely records the calling arguments.
#
#             """
#             @cherrypy.expose
#             def index(self, *args, **kwargs):
#                 self.args = args
#                 self.kwargs = kwargs
#
#             self.socket_port = port
#
#         self.receiver = RequestReceiver()
#
#         cherrypy.quickstart(self.receiver)
#
#     if sys.version_info < (2, 7):
#         """Add a poor man's forward compatibility."""
#
#         class ContainsError(AssertionError):
#             pass
#
#         def assertIn(self, a, b):
#             if not a in b:
#                 raise self.ContainsError("%s not in %s" % (a, b))
#
# class TestClientInitialRequest(SantiagoTest):
#     """Does the client send a correctly formed request?
#
#     In these tests, we're sending requests to a mock listener which merely
#     records that the requests were well-formed.
#
#     """
#     def setUp(self):
#         super(SantiagoTest, self).setUp()
#
#         self.serveOnPort(8000)
#
#     def test_request(self):
#         """Verify that A queues a properly formatted initial request."""
#
#         self.santiago_a.request(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to="localhost:9001")
#
#         self.assertEqual(self.santiago_a.outgoing_messages,
#                          [{ "from": "a", "to": "b",
#                             "client": "a", "host": "b",
#                             "service": "wiki", "reply-to": "localhost:9001"}])
#
#     def test_request(self):
#         """Verify that A sends out a properly formatted initial request."""
#
#         self.santiago_a.request(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to="localhost:9001")
#
#         self.santiago_a.process()
#
#         self.assertEqual(self.receiver.kwargs,
#                          [{ "from": "a", "to": "b",
#                             "client": "a", "host": "b",
#                             "service": "wiki", "reply-to": "localhost:9001"}])
#
# class TestServerInitialRequest(SantiagoTest):
#     """Test how the Santiago server replies to initial service requests.
#
#     TODO: Add a mock listener to represent A.
#     TODO: Transform the data structure tests into the mock-response tests.
#     TODO tests: (normal serving + proxying) * (learning santiagi + not learning)
#
#     Proxying
#     ~~~~~~~~
#
#     A host/listener (B) trusts proxied requests according to the minimum trust
#     in the request.  If the request comes from an untrusted proxy or is for an
#     untrusted client, B ignores it.
#
#     """
#     def setUp(self):
#         super(SantiagoTest, self).setUp()
#
#         self.serveOnPort(9000)
#
#     def test_acknowledgement(self):
#         """If B receives an authorized request, then it replies with a location.
#
#         An "authorized request" in this case is for a service from a client that
#         B is willing to host that service for.
#
#         In this case, B will answer with the wiki's location.
#
#         """
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages,
#                          [{"from": "b",
#                            "to": "a",
#                            "client": "a",
#                            "host": "b",
#                            "service": "wiki",
#                            "locations": ["192.168.0.13"],
#                            "reply-to": "localhost:8000"}])
#
#     def test_reject_bad_service(self):
#         """Does B reject requests for unsupported services?
#
#         In this case, B should reply with an empty list of locations.
#
#         """
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages,
#                          [{"from": "b",
#                            "to": "a",
#                            "client": "a",
#                            "host": "b",
#                            "service": "wiki",
#                            "locations": [],
#                            "reply-to": "localhost:8000"}])
#
#     def test_reject_bad_key(self):
#         """If B receives a request from an unauthorized key, it does not reply.
#
#         An "unauthorized request" in this case is for a service from a client
#         that B does not trust.  This is different than clients B hosts no
#         services for.
#
#         In this case, B will never answer the request.
#
#         """
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="z", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages, [])
#
#     def test_reject_good_source_bad_client(self):
#         """B is silent when a trusted key proxies anything for an untrusted key.
#
#         B doesn't know who the client is and should consider it an
#         untrusted key connection attempt.
#
#         """
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="z", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages, [])
#
#     def test_reject_bad_source_good_client(self):
#         """B is silent when an untrusted key proxies anything for a trusted key.
#
#         B doesn't know who the proxy is and should consider it an
#         untrusted key connection attempt.
#
#         """
#         self.santiago_b.receive(from_="z", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages, [])
#
#     def test_reject_bad_source_bad_client(self):
#         """B is silent when untrusted keys proxy anything for untrusted keys.
#
#         B doesn't know who anybody is and considers this an untrusted
#         connection attempt.
#
#         """
#         self.santiago_b.receive(from_="y", to="b",
#                                 client="z", host="b",
#                                 service="wiki", reply_to=None)
#
#         self.assertEqual(self.santiago_b.outgoing_messages, [])
#
#     def test_learn_santaigo(self):
#         """Does B learn new Santiago locations from trusted requests?
#
#         If A sends B a request with a new Santiago location, B should learn it.
#
#         """
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to="localhost:9001")
#
#         self.assertEqual(self.santiago_b.consuming["santiago"]["a"],
#                          ["localhost:9000", "localhost:9001"])
#
#     def test_handle_requests_once(self):
#         """Verify that we reply to each request only once."""
#
#         self.santiago_b.receive(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to=None)
#         self.santiago_b.process()
#
#         self.assertEqual(self.santiago_b.outgoing_messages, [])
#
# class TestServerInitialResponse(SantiagoTest):
#     pass
#
# class TestClientInitialResponse(SantiagoTest):
#     pass
#
# class TestForwardedRequest(SantiagoTest):
#     pass
#
# class TestForwardedResponse(SantiagoTest):
#     pass
#
# class TestSimpleSantiago(unittest.TestCase):
#     def setUp(self):
#
#         port_a = "localhost:9000"
#         port_b = "localhost:8000"
#
#         listeners_a = {"http": {"port": port_a}}
#         senders_a = ({ "protocol": "http", "proxy": tor_proxy_port },)
#
#         listeners_b = {"http": {"port": port_b}}
#         senders_b = ({ "protocol": "http", "proxy": tor_proxy_port },)
#
#         hosting_a = { "b": { "santiago": set( ["aDifferentHexNumber.onion"])}}
#         consuming_a = { "santiagao": {"b": set(["iAmAHexadecimalNumber.onion"])}}
#
#         hosting_b = { "a": { "santiago": set( ["iAmAHexadecimalNumber.onion"])}}
#         consuming_b = { "santiagao": { "a": set( ["aDifferentHexNumber.onion"])}}
#
#         self.santiago_a = santiago.Santiago(listeners_a, senders_a,
#                                          hosting_a, consuming_a, "a")
#         self.santiago_b = santiago.Santiago(listeners_b, senders_b,
#                                          hosting_b, consuming_b, "b")
#
#         cherrypy.Application(self.santiago_a, "/")
#         cherrypy.Application(self.santiago_b, "/")
#
#         cherrypy.engine.start()
#
#     def testRequest(self):
#         self.santiago_a.request(from_="a", to="b",
#                                 client="a", host="b",
#                                 service="wiki", reply_to="localhost:9000")
#
#
# class Unwrapping(unittest.TestCase):
#
#     def testVerifySigner(self):
#         pass
#
#     def testVerifyClient(self):
#         pass
#
#     def testDecryptClient(self):
#         pass
#
# class IncomingProxyRequest(unittest.TestCase):
#
#     """Do we correctly handle valid, incoming, proxied messages?
#
#     These tests are for the first wrapped layer of the message, that which is
#     signed by the sender.  The sender is not necessarily the original requester
#     who's asking us to do something with the message.
#
#     """
#
#     def setUp(self):
#         pass
#
#     def testPassingMessage(self):
#         """Does a valid proxied message pass?"""
#
#         pass
#
#     def testInvalidSig(self):
#         """Does an invalid signature raise an error?"""
#
#         pass
#
#     def testUnknownClient(self):
#         """Does an unknown client raise an error?"""
#
#         pass
#
# class IncomingSignedRequest(IncomingProxyRequest):
#
#     """Do we correctly handle valid, incoming, messages?
#
#     These tests focus on the second layer of the message which is signed by the
#     host/client and lists a destination.
#
#     """
#     def testProxyOtherHosts(self):
#         """Messages to others are sent to them directly or proxied."""
#
#         pass
#
#     def testHandleMyHosting(self):
#         """Messages to me are not proxied and handled normally."""
#
#         pass
#
#     def testNoDestination(self):
#         """Messages without destinations are ignored."""
#
#         pass
#
# class IncomingRequestBody(IncomingSignedRequest):
#
#     """Do we correctly handle the body of a request?
#
#     This is the last layer of the message which is encrypted by the original
#     sender.  This validation also depends on the previous layer's data, making
#     it a bit more complicated.
#
#     """
#     def testHandleGoodMessage(self):
#         """Sanity check: no errors are thrown for a valid message."""
#
#         pass
#
#     def testCantDecryptMessage(self):
#         """This message isn't for me.  I can't decrypt it."""
#
#         pass
#
#     def testImNotHost(self):
#         """Bail out if someone else is the host, yet I am the "to"."""
#
#         pass
#
#     def testImNotClient(self):
#         """Bail out if someone else is the client, yet I am the "to"."""
#
#         pass
#
#     def testHostAndClient(self):
#         """Bail out if the message includes a host and a client.
#
#         A circular response?
#
#         """
#         pass
#
#     def testImNotTo(self):
#         """This message isn't for me.
#
#         The "To" has been repeated from the signed message, but I'm not the
#         recipient in the encrypted message.
#
#         """
#         pass
#
#     def testNoDestinations(self):
#         """No host, client, or to."""
#
#         pass
#
#     def testSignersDiffer(self):
#         """The signed message and encrypted message have different signers."""
#
#         pass
#
#     def testSignerAndClientDiffer(self):
#         """The encrypted message is signed by someone other than the cilent."""
#
#         pass


class VerifyRequest(unittest.TestCase):

    """Are incoming requests handled correctly?

    - Messages come with a request.
    - Each message identifies the Santiago protocol version it uses.
    - Messages come with a range of Santiago protocol versions I can reply with.
    - Messages that don't share any of my versions are ignored (either the
      client or I won't be able to understand the message).

    Test this in a fairly hacky way.

    """
    def setUp(self):
        self.santiago = santiago.Santiago()
        self.request = { "request_version": 1,
                         "reply_versions": [1],
                         "request": None }

    def test_valid_message(self):
        """A known good request passes."""

        self.assertTrue(self.santiago.verify_request(self.request))

    def test_required_keys_are_required(self):
        """Messages without required keys fail.

        The following keys are required in the un-encrypted part of the message:

        - request
        - request_version
        - reply_versions

        """
        for key in ("request", "request_version", "reply_versions"):
            del self.request[key]

            self.assertFalse(self.santiago.verify_request(self.request))

    def test_require_protocol_version_overlap(self):
        """Clients that can't accept protocols I can send are ignored."""

        santiago.Santiago.SUPPORTED_PROTOCOLS, unsupported = \
            set(["e"]), santiago.Santiago.SUPPORTED_PROTOCOLS

        self.assertFalse(self.santiago.verify_request(self.request))

        santiago.Santiago.SUPPORTED_PROTOCOLS, unsupported = \
            unsupported, santiago.Santiago.SUPPORTED_PROTOCOLS

    def test_require_protocol_version_understanding(self):
        """I must ignore any protocol versions I can't understand."""

        self.request["request_version"] = "e"

        self.assertFalse(self.santiago.verify_request(self.request))


class UnpackRequest(unittest.TestCase):

    """Are requests unpacked as expected?

    - Messages that aren't for me (that I can't decrypt) are ignored.
    - Messages with invalid signatures are rejected.
    - Only passing messages return the dictionary.
    - The message is unpacked correctly.  This is a bit difficult because of the
      number of overlapping data types.

      First, we have the keys that must be present in each message:

      - client
      - host
      - service
      - locations
      - reply_to
      - request_version
      - reply_versions

      Next the list-keys which must be lists (they'll later be converted
      directly to sets):

      - reply_to
      - locations
      - reply_versions

      Finally, we have the keys that may be empty:

      - locations
      - reply_to

      ``locations`` is empty on an incoming (request) message, while
      ``reply_to`` may be assumed if the reply destinations haven't changed
      since the previous message.  If they have, and the client still doesn't
      send the reply_to, then the host will be unable to communicate with it, so
      it's in the client's best interests to send it whenever reasonable.

      So, the structure of a message is a little weird here.  We have three sets
      of overlapping requirements:

      #. Certain keys must be present.
      #. Certain keys must be lists.
      #. Certain keys may be unset.

      The really odd ones out are "locations" and "reply_to", which fall into
      all three categories.

    """
    def setUp(self):
        """Create a request."""

        self.gpg = gnupg.GPG(use_agent = True)

        self.keyid = utilities.load_config().get("pgpprocessor", "keyid")

        self.santiago = santiago.Santiago(me = self.keyid)

        self.request = { "host": self.keyid, "client": self.keyid,
                         "service": "santiago", "reply_to": [1],
                         "locations": [1],
                         "request_version": 1, "reply_versions": [1], }

        self.ALL_KEYS = ("host", "client", "service", "locations", "reply_to",
                         "request_version", "reply_versions")
        self.REQUIRED_KEYS = ("client", "host", "service",
                              "request_version", "reply_versions")
        self.OPTIONAL_KEYS = ("locations", "reply_to")
        self.LIST_KEYS = ("reply_to", "locations", "reply_versions")

    def test_valid_message(self):
        """A message that should pass does pass normally."""

        adict = self.validate_request(dict(self.request))
        self.request = self.wrap_message(self.request)

        self.assertEqual(self.santiago.unpack_request(str(self.request)), adict)

    def validate_request(self, adict):
        # convert non-None elements to sets, like unpack does.
        adict.update(dict([ (k, set(adict[k])) for
                            k in self.LIST_KEYS
                            if adict[k] is not None ]))
        adict.update({ "from": self.keyid,
                       "to": self.keyid })

        return adict

    def test_request_contains_all_keys(self):
        """The test request needs all supported keys."""

        for key in self.ALL_KEYS:
            self.assertTrue(key in self.request)

    def wrap_message(self, message):
        """The standard wrapping method for these tests."""

        return str(self.gpg.encrypt(str(message),
                                    recipients=[self.keyid],
                                    sign=self.keyid))

    def test_key_lists_updated(self):
        """Are the lists of keys up-to-date?"""

        for key in ("ALL_KEYS", "REQUIRED_KEYS", "OPTIONAL_KEYS", "LIST_KEYS"):
            self.assertEqual(getattr(self, key),
                             getattr(santiago.Santiago, key))

    def test_all_keys_accounted_for(self):
        """All the keys in the ALL_KEYS list are either required or optional."""

        self.assertEqual(set(self.ALL_KEYS),
                         set(self.REQUIRED_KEYS) | set(self.OPTIONAL_KEYS))

    def test_requred_keys_are_required(self):
        """If any required keys are missing, the message is skipped."""

        for key in self.ALL_KEYS:
            broken_dict = dict(self.request)
            del broken_dict[key]
            encrypted_data = self.wrap_message(str(broken_dict))

            self.assertEqual(
                self.santiago.unpack_request(str(encrypted_data)),
                None)

    def test_non_null_keys_are_set(self):
        """If any keys that can't be empty are empty, the message is skipped."""

        for key in self.REQUIRED_KEYS:
            broken_dict = dict(self.request)
            broken_dict[key] = None
            encrypted_data = self.wrap_message(str(broken_dict))

            self.assertEqual(
                self.santiago.unpack_request(str(encrypted_data)),
                None)

    def test_null_keys_are_null(self):
        """If any optional keys are null, the message's still processed."""

        for key in self.OPTIONAL_KEYS:
            broken_dict = dict(self.request)
            broken_dict[key] = None
            encrypted_data = str(self.wrap_message(str(broken_dict)))

            broken_dict = self.validate_request(broken_dict)

            self.assertEqual(
                self.santiago.unpack_request(encrypted_data),
                broken_dict)

    def test_skip_undecryptable_messages(self):
        """Mesasges that I can't decrypt (for other folks) are skipped.

        I don't know how I'll encrypt to a key that isn't there though.

        """
        pass

    def test_skip_invalid_signatures(self):
        """Messages with invalid signatures are skipped."""

        self.request = self.wrap_message(str(self.request))

        # delete the 7th line for the fun of it.
        mangled = self.request.splitlines(True)
        del mangled[7]
        self.request = "".join(mangled)

        self.assertEqual(self.santiago.unpack_request(self.request), None)

    def test_incoming_lists_are_lists(self):
        """Any variables that must be lists, before processing, actually are."""

        for key in self.LIST_KEYS:
            broken_request = dict(self.request)
            broken_request[key] = 1
            broken_request = self.wrap_message(str(broken_request))

            self.assertEqual(self.santiago.unpack_request(broken_request), None)

    def test_sets_are_sets(self):
        """Any variables that must be sets, after processing, actually are."""

        self.request = self.wrap_message(str(self.request))

        unpacked = self.santiago.unpack_request(self.request)

        for key in self.LIST_KEYS:
            for attribute in ("union", "intersection"):
                self.assertTrue(hasattr(unpacked[key], attribute))

class HandleRequest(unittest.TestCase):
    """Process an incoming request, from a client, for to host services.

    - Verify we're willing to host for both the client and proxy.  If we
      aren't, quit and return nothing.
    - Forward the request if it's not for me.
    - Learn new Santiagi if they were sent.
    - Reply to the client on the appropriate protocol.

    """
    def setUp(self):
        """Do a good bit of setup to make this a nicer test-class.

        Successful tests will call ``Santiago.outgoing_request``, so that's
        overridden to record that the method is called.

        """
        self.keyid = utilities.load_config().get("pgpprocessor", "keyid")

        self.santiago = santiago.Santiago(
            hosting = {self.keyid: {"santiago": set([1]) }},
            consuming = {"santiago": {self.keyid: set([1]) }},
            me = self.keyid)

        self.santiago.requested = False
        self.santiago.outgoing_request = (lambda *args, **kwargs:
                                              self.record_success())

        self.from_ = self.keyid
        self.to = self.keyid
        self.host = self.keyid
        self.client = self.keyid
        self.service = "santiago"
        self.reply_to = set([1])
        self.request_version = 1
        self.reply_versions = set([1])

    def record_success(self):
        """Record that we tried to reply to the request."""

        self.santiago.requested = True

    def test_call(self):
        """A short-hand for calling handle_request with all 8 arguments.  Oy."""

        self.santiago.handle_request(
                self.from_, self.to,
                self.host, self.client,
                self.service, self.reply_to,
                self.request_version, self.reply_versions)

    def test_valid_message(self):
        """Reply to valid messages."""

        self.test_call()

        self.assertTrue(self.santiago.requested)

    def test_unwilling_client(self):
        """Don't handle the request if the cilent isn't trusted."""

        self.client = 0

        self.test_call()

        self.assertFalse(self.santiago.requested)

    def test_unwilling_proxy(self):
        """Don't handle the request if the proxy isn't trusted."""

        self.from_ = 0

        self.test_call()

        self.assertFalse(self.santiago.requested)

    def test_learn_services(self):
        """New reply_to locations are learned."""

        self.reply_to.update([2])

        self.test_call()

        self.assertTrue(self.santiago.requested)
        self.assertEqual(self.santiago.consuming["santiago"][self.keyid],
                         set([1, 2]))


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    unittest.main()
