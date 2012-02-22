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
import santiago
# TODO import some http client and validate my responses!

class TestInitialRequest(unittest.TestCase):
    """Testing the initial request.

    Does Santiago produce well-formed output when creating a service request?

    """
    def setup(self):
        requester = santiago.SantiagoSender("initial_requester")
        destination = santiago.SantiagoListener("initial_destination",8081)

    def test_valid_request(self):
        """When requested, does Santiago send out an appropriate message?"""

        # TODO finish these and otehr tests
        requester.request(destination="james", service="wiki")
        
class TestInitialResponse(unittest.TestCase):
    pass

class TestForwardedRequest(unittest.TestCase):
    pass

class TestForwardedResponse(unittest.TestCase):
    pass
