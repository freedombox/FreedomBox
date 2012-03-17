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

"""

import unittest
from protocols.http import SantiagoHttpSender, SantiagoHttpListener
import santiago
import sys


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

    if sys.version_info < (2, 7):
        """Add a poor man's forward compatibility."""

        class ContainsError(AssertionError):
            pass

        def assertIn(self, a, b):
            if not a in b:
                raise self.ContainsError("%s not in %s" % (a, b))

class TestServerInitialRequest(SantiagoTest):
    """Test how the Santiago server replies to initial service requests.

    TODO: Add a mock listener to represent A.
    TODO: Transform the data structure tests into the mock-response tests.
    TODO tests: (normal serving + proxying) * (learning santiagi + not learning)
    
    """
    def test_acknowledgement(self):
        """If B receives an authorized request, then it replies with a location.

        An "authorized request" in this case is for a service from a client that
        B is willing to host that service for.

        In this case, B will answer with the wiki's location.

        """
        self.santiago_b.receive(from_=None, to=None,
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

    def test_negative_acknowledgement_bad_service(self)
        """Does B reject requests for unsupported services?

        In this case, B should reply with an empty list of locations.

        """
        self.santiago_b.receive(from_=None, to=None,
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

    def test_deny_bad_key(self):
        """If B receives a request from an unauthorized key, it does not reply.

        An "unauthorized request" in this case is for a service from a client
        that B does not trust.  This is different than clients B hosts no
        services for.

        In this case, B will never answer the request.

        """
        self.santiago_b.receive(from_=None, to=None,
                                client="z", host="b",
                                service="wiki", reply_to=None)

        self.assertEqual(self.santiago_b.outgoing_messages, [])

    def test_learn_santaigo(self):
        """Does B learn new Santiago locations from trusted requests?

        If A sends B a request with a new Santiago location, B should learn it.

        """
        self.santiago_b.receive(from_=None, to=None,
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.assertEqual(self.santiago_b.consuming["santiago"]["a"],
                         ["localhost:9000", "localhost:9001"])

    def test_handle_requests_once(self):
        """Verify that we reply to each request only once."""

        self.santiago_b.receive(from_=None, to=None,
                                client="a", host="b",
                                service="wiki", reply_to=None)
        self.santiago_b.process()

        self.assertEqual(self.santiago_b.outgoing_messages, [])

class TestClientInitialRequest(SantiagoTest):
    """Does the client send a correctly formed request?

    In these tests, we're sending requests to a mock listener which merely
    records that the requests were well-formed.

    """
    def setUp(self):
        super(SantiagoTest, self).setUp()

        import cherrypy
        class RequestReceiver(object):

            def index(self, *args, **kwargs):
                self.args = *args
                self.kwargs = **kwargs

            index.exposed = True
            self.socket_port = 8000

        self.receiver = RequestReceiver()
        cherrypy.quickstart(self.receiver)

    def test_request(self):
        """Verify that A queues a properly formatted initial request."""

        self.santiago_a.request(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.assertEqual(self.santiago_a.outgoing_messages,
                         [{ "from": "a", "to": "b",
                            "client": "a", "host": "b",
                            "service": "wiki", "reply-to": "localhost:9001"})]

    def test_request(self):
        """Verify that A sends out a properly formatted initial request."""

        self.santiago_a.request(from_="a", to="b",
                                client="a", host="b",
                                service="wiki", reply_to="localhost:9001")

        self.santiago_a.process()

        self.assertEqual(self.receiver.kwargs,
                         [{ "from": "a", "to": "b",
                            "client": "a", "host": "b",
                            "service": "wiki", "reply-to": "localhost:9001"})]

class TestServerInitialResponse(SantiagoTest):
    pass

class TestClientInitialResponse(SantiagoTest):
    pass

class TestForwardedRequest(SantiagoTest):
    pass

class TestForwardedResponse(SantiagoTest):
    pass


if __name__ == "__main__":
    unittest.main()
