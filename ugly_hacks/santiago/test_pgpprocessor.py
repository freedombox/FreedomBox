#! /usr/bin/python

"""Tests for the PGP Processing Tools.

All aspects of each PGP processor should be fully tested: this verifies
identity, allowing trust to exist in the system.  If this is mucked up, there
can be no trustworthy trust.

"""

from pprint import pprint

import ConfigParser as configparser
import gnupg
import pgpprocessor
import unittest

class ProcessorCase(unittest.TestCase):
    """The superclass for pgpprocessor tests, containing shared setup:

    - Sign a message several times with a specified key.

    """
    MESSAGES = [ str({"host": "somebody"}), ]
    GPG = gnupg.GPG(use_agent = True)

    CONFIG = configparser.ConfigParser({"KEYID": "0928D23A"})
    CONFIG.read(["test.cfg"])
    KEYID = CONFIG.get("pgpprocessor", "keyid")
    
    # sign the message a few times.
    for i in range(0, 3):
        MESSAGES.append(str(GPG.sign(MESSAGES[i], keyid = KEYID)))

class UnwrapperTest(ProcessorCase):
    """Verify that we can unwrap multiply-signed PGP messages correctly.

    """
    def setUp(self):
        self.messages = list(ProcessorCase.MESSAGES)
        self.unwrapper = pgpprocessor.Unwrapper(self.messages[-1],
                                                ProcessorCase.GPG)

    def test_creating_message_doesnt_unwrap(self):
        """Creating an unwrapper shouldn't unwrap the message.

        Only iterating through the unwrapper should unwrap it.  We don't want to
        process the message at all until we're explicitly told to do so.

        """
        self.assertEqual(self.unwrapper.message, self.messages[-1])
        self.assertEqual(str(self.unwrapper).strip(), "")

    def test_iterator_unwraps_correctly(self):
        """The iterator should correctly unwrap each stage of the message."""

        for i, message in enumerate(self.unwrapper):
            self.assertEqual(message, self.messages[-i-2])

    def test_original_message(self):
        """Unwrapper.original_message actually returns the original message."""

        print (self.unwrapper.message)
        self.assertEqual(self.unwrapper.next(), self.messages[-1])


if __name__ == "__main__":
    unittest.main()
