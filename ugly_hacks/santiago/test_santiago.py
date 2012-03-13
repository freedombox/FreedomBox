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
        self.santiago = santiago.Santiago("0x1")

    if sys.version_info < (2, 7):
        """Add a poor man's forward compatibility."""

        class ContainsError(AssertionError):
            pass

        def assertIn(self, a, b):
            if not a in b:
                raise self.ContainsError("%s not in %s" % (a, b))

class TestDataModel(SantiagoTest):
    """Test adding and removing services and data."""

    def test_add_listener(self):
        """Verify that we can add a listener."""

        http_listener = SantiagoHttpListener(self.santiago, "localhost:8080")
        self.santiago.add_listener(http_listener)

        self.assertIn(http_listener, self.santiago.listeners)

    def test_add_sender(self):
        """Verify that we can add a sender."""

        http_sender = SantiagoHttpSender(self.santiago)
        self.santiago.add_sender(http_sender)

        self.assertIn(http_sender, self.santiago.senders)

    def test_provide_at_location(self):
        """Verify that we can provide a service somewhere."""

        service, location = ("something", "there")
        self.santiago.provide_at_location(service, location)

        self.assertIn(location, self.santiago.hosting[service])

    def test_provide_for_key(self):
        """Verify we can provide a specific service to someone."""

        service, key = ("something", "0x1")
        self.santiago.provide_for_key(service, key)

        self.assertIn(service, self.santiago.keys[key])


class TestServing(SantiagoTest):
    """TODO: tests for:

    (normal serving + proxying) * (learning santiagi + not learning)

    """
    def setUp(self):
        super(TestServing, self).setUp()

        self.santiago.provide_at_location("wiki", "192.168.0.13")
        self.santiago.provide_for_key("wiki", "0x2")

        self.listener = santiago.SantiagoListener(self.santiago, "localhost:8080")
        self.sender = santiago.SantiagoSender(self.santiago)
        self.santiago.add_listener(self.listener)
        self.santiago.add_sender(self.sender)

    def test_successful_serve(self):
        """Make sure we get an expected, successful serving message back."""

        self.listener.serve("0x2", "wiki", "0x1", 0, None)
        expected = [
            { "to": "0x2",
              "location": ["192.168.0.13"],
              "reply-to": self.listener.location, }, ]

        self.assertEqual(self.sender.send(), expected)


class TestConsuming(SantiagoTest):
    """TODO: tests for:

    (learning services)

    """
    pass

class TestInitialRequest(SantiagoTest):
    """Testing the initial request.

    Does Santiago produce well-formed output when creating a service request?

    """
    pass

class TestInitialResponse(SantiagoTest):
    pass

class TestForwardedRequest(SantiagoTest):
    pass

class TestForwardedResponse(SantiagoTest):
    pass


if __name__ == "__main__":
    unittest.main()
