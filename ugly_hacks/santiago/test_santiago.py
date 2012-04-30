#! /usr/bin/python  -*- mode: autofill; fill-column: 80 -*-


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


import unittest
import os
import sys

from pprint import pprint
sys.path.extend(["../..", ".",
                 "/home/nick/programs/python-gnupg/python-gnupg-0.2.9"])
import gnupg
import simplesantiago


class SantiagoTest(unittest.TestCase):
    """The base class for tests."""

    def setUp(self):
        super(TestServing, self).setUp()

        port_a = "localhost:9000"
        port_b = "localhost:8000"

        listeners_a = [santiago.SantiagoListener(port_a)]
        senders_a = [santiago.SantiagoSender()]
        listeners_b = [santiago.SantiagoListener(port_b)]
        senders_b = [santiago.SantiagoSender()]

        hosting_a = { "b": { "santiago": [ port_a ]}}
        consuming_a = { "santiagao": { "b": [ port_b ]}}

        hosting_b = { "a": { "santiago": [ port_b ],
                             "wiki": [ "localhost:8001" ]}}
        consuming_b = { "santiagao": { "a": [ port_a ]}}

        self.santiago_a = Santiago(listeners_a, senders_a, hosting_a, consuming_a)
        self.santiago_b = Santiago(listeners_b, senders_b, hosting_b, consuming_b)

    def serveOnPort(self, port):
        """Start listening for connections on a named port.

        Used in testing as a mock listener for responses from a Santiago server.

        """
        class RequestReceiver(object):
            """A very basic listener.

            It merely records the calling arguments.

            """
            @cherrypy.expose
            def index(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            self.socket_port = port

        self.receiver = RequestReceiver()

        cherrypy.quickstart(self.receiver)

    if sys.version_info < (2, 7):
        """Add a poor man's forward compatibility."""

        class ContainsError(AssertionError):
            pass

        def assertIn(self, a, b):
            if not a in b:
                raise self.ContainsError("%s not in %s" % (a, b))

class TestClientInitialRequest(SantiagoTest):
    """Does the client send a correctly formed request?

    In these tests, we're sending requests to a mock listener which merely
    records that the requests were well-formed.

    """
    def setUp(self):
        super(SantiagoTest, self).setUp()

        self.serveOnPort(8000)

    def test_request(self):
        """Verify that A queues a properly formatted initial request."""

        self.santiago_a.request(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.assertEqual(self.santiago_a.outgoing_messages,
                         [{ "from": "a", "to": "b",
                            "client": "a", "host": "b",
                            "service": "wiki", "reply-to": "localhost:9001"}])

    def test_request(self):
        """Verify that A sends out a properly formatted initial request."""

        self.santiago_a.request(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.santiago_a.process()

        self.assertEqual(self.receiver.kwargs,
                         [{ "from": "a", "to": "b",
                            "client": "a", "host": "b",
                            "service": "wiki", "reply-to": "localhost:9001"}])

class TestServerInitialRequest(SantiagoTest):
    """Test how the Santiago server replies to initial service requests.

    TODO: Add a mock listener to represent A.
    TODO: Transform the data structure tests into the mock-response tests.
    TODO tests: (normal serving + proxying) * (learning santiagi + not learning)

    Proxying
    ~~~~~~~~

    A host/listener (B) trusts proxied requests according to the minimum trust
    in the request.  If the request comes from an untrusted proxy or is for an
    untrusted client, B ignores it.

    """
    def setUp(self):
        super(SantiagoTest, self).setUp()

        self.serveOnPort(9000)

    def test_acknowledgement(self):
        """If B receives an authorized request, then it replies with a location.

        An "authorized request" in this case is for a service from a client that
        B is willing to host that service for.

        In this case, B will answer with the wiki's location.

        """
        self.santiago_b.receive(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages,
                         [{"from": "b",
                           "to": "a",
                           "client": "a",
                           "host": "b",
                           "service": "wiki",
                           "locations": ["192.168.0.13"],
                           "reply-to": "localhost:8000"}])

    def test_reject_bad_service(self):
        """Does B reject requests for unsupported services?

        In this case, B should reply with an empty list of locations.

        """
        self.santiago_b.receive(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages,
                         [{"from": "b",
                           "to": "a",
                           "client": "a",
                           "host": "b",
                           "service": "wiki",
                           "locations": [],
                           "reply-to": "localhost:8000"}])

    def test_reject_bad_key(self):
        """If B receives a request from an unauthorized key, it does not reply.

        An "unauthorized request" in this case is for a service from a client
        that B does not trust.  This is different than clients B hosts no
        services for.

        In this case, B will never answer the request.

        """
        self.santiago_b.receive(from_="a", to="b",
                                client="z", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages, [])

    def test_reject_good_source_bad_client(self):
        """B is silent when a trusted key proxies anything for an untrusted key.

        B doesn't know who the client is and should consider it an
        untrusted key connection attempt.

        """
        self.santiago_b.receive(from_="a", to="b",
                                client="z", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages, [])

    def test_reject_bad_source_good_client(self):
        """B is silent when an untrusted key proxies anything for a trusted key.

        B doesn't know who the proxy is and should consider it an
        untrusted key connection attempt.

        """
        self.santiago_b.receive(from_="z", to="b",
                                client="a", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages, [])

    def test_reject_bad_source_bad_client(self):
        """B is silent when untrusted keys proxy anything for untrusted keys.

        B doesn't know who anybody is and considers this an untrusted
        connection attempt.

        """
        self.santiago_b.receive(from_="y", to="b",
                                client="z", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages, [])

    def test_learn_santaigo(self):
        """Does B learn new Santiago locations from trusted requests?

        If A sends B a request with a new Santiago location, B should learn it.

        """
        self.santiago_b.receive(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.assertEqual(self.santiago_b.consuming["santiago"]["a"],
                         ["localhost:9000", "localhost:9001"])

    def test_handle_requests_once(self):
        """Verify that we reply to each request only once."""

        self.santiago_b.receive(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to=None)
        self.santiago_b.process()

        self.assertEqual(self.santiago_b.outgoing_messages, [])

class TestServerInitialResponse(SantiagoTest):
    pass

class TestClientInitialResponse(SantiagoTest):
    pass

class TestForwardedRequest(SantiagoTest):
    pass

class TestForwardedResponse(SantiagoTest):
    pass

class TestSimpleSantiago(unittest.TestCase):
    def setUp(self):

        port_a = "localhost:9000"
        port_b = "localhost:8000"

        listeners_a = {"http": {"port": port_a}}
        senders_a = ({ "protocol": "http", "proxy": tor_proxy_port },)

        listeners_b = {"http": {"port": port_b}}
        senders_b = ({ "protocol": "http", "proxy": tor_proxy_port },)

        hosting_a = { "b": { "santiago": set( ["aDifferentHexNumber.onion"])}}
        consuming_a = { "santiagao": {"b": set(["iAmAHexadecimalNumber.onion"])}}

        hosting_b = { "a": { "santiago": set( ["iAmAHexadecimalNumber.onion"])}}
        consuming_b = { "santiagao": { "a": set( ["aDifferentHexNumber.onion"])}}

        self.santiago_a = SimpleSantiago(listeners_a, senders_a,
                                         hosting_a, consuming_a, "a")
        self.santiago_b = SimpleSantiago(listeners_b, senders_b,
                                         hosting_b, consuming_b, "b")

        cherrypy.Application(self.santiago_a, "/")
        cherrypy.Application(self.santiago_b, "/")

        cherrypy.engine.start()

    def testRequest(self):
        self.santiago_a.request(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9000")


class Unwrapping(unittest.TestCase):

    def testVerifySigner(self):
        pass

    def testVerifyClient(self):
        pass

    def testDecryptClient(self):
        pass

class IncomingProxyRequest(unittest.TestCase):

    """Do we correctly handle valid, incoming, proxied messages?

    These tests are for the first wrapped layer of the message, that which is
    signed by the sender.  The sender is not necessarily the original requester
    who's asking us to do something with the message.

    """

    def setUp(self):
        pass

    def testPassingMessage(self):
        """Does a valid proxied message pass?"""

        

        pass

    def testInvalidSig(self):
        """Does an invalid signature raise an error?"""

        pass

    def testUnknownClient(self):
        """Does an unknown client raise an error?"""

        pass

class IncomingSignedRequest(IncomingProxyRequest):

    """Do we correctly handle valid, incoming, messages?

    These tests focus on the second layer of the message which is signed by the
    host/client and lists a destination.

    """
    def testProxyOtherHosts(self):
        """Messages to others are sent to them directly or proxied."""

        pass

    def testHandleMyHosting(self):
        """Messages to me are not proxied and handled normally."""

        pass

    def testNoDestination(self):
        """Messages without destinations are ignored."""

        pass

class IncomingRequestBody(IncomingSignedRequest):

    """Do we correctly handle the body of a request?

    This is the last layer of the message which is encrypted by the original
    sender.  This validation also depends on the previous layer's data, making
    it a bit more complicated.

    """
    def testHandleGoodMessage(self):
        """Sanity check: no errors are thrown for a valid message."""

        pass

    def testCantDecryptMessage(self):
        """This message isn't for me.  I can't decrypt it."""

        pass

    def testImNotHost(self):
        """Bail out if someone else is the host, yet I am the "to"."""

        pass

    def testImNotClient(self):
        """Bail out if someone else is the client, yet I am the "to"."""

        pass

    def testHostAndClient(self):
        """Bail out if the message includes a host and a client.

        A circular response?

        """
        pass

    def testImNotTo(self):
        """This message isn't for me.

        The "To" has been repeated from the signed message, but I'm not the
        recipient in the encrypted message.

        """
        pass

    def testNoDestinations(self):
        """No host, client, or to."""

        pass

    def testSignersDiffer(self):
        """The signed message and encrypted message have different signers."""

        pass

    def testSignerAndClientDiffer(self):
        """The encrypted message is signed by someone other than the cilent."""

        pass

def show(name, item, iterations=1):
    print "#" * iterations, name, "#" * iterations
    if hasattr(item, "__dict__"):
        for k, v in item.__dict__.iteritems():
            show(k, v, iterations + 1)
    elif type(item) in (str, unicode):
        print item
    else:
        pprint(item)

if __name__ == "__main__":
    unittest.main()
