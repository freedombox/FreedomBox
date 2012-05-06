#! /usr/bin/python

"""Tests for the PGP Processing Tools.

All aspects of each PGP processor should be fully tested: this verifies
identity, allowing trust to exist in the system.  If this is mucked up, trust
isn't verifiable.

"""

import ConfigParser as configparser
import gnupg
import pgpprocessor
import unittest

ITERATIONS = 3

def remove_line(string, line, preserve_newlines = True):
    """Remove a line from a multi-line string."""

    if preserve_newlines and not line.endswith("\n"):
        line += "\n"

    return str(string.splitlines(preserve_newlines).remove(line))

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
    for i in range(ITERATIONS):
        MESSAGES.append(str(GPG.sign(MESSAGES[i], keyid = KEYID)))

class UnwrapperTest(ProcessorCase):
    """Verify that we can unwrap multiply-signed PGP messages correctly."""

    def setUp(self):
        self.messages = list(ProcessorCase.MESSAGES)
        self.unwrapper = pgpprocessor.Unwrapper(self.messages[-1],
                                                ProcessorCase.GPG)

    def test_messages_wrapped(self):
        """Were the messages correctly wrapped in the first place?"""

        self.assertEqual(ITERATIONS + 1, len(self.messages))

    def test_unwrap_all_messages(self):
        """Do we unwrap the right number of messages?"""

        # count each element in the iterator once, skipping the first.
        self.assertEqual(ITERATIONS, sum([1 for e in self.unwrapper]))

    def test_dont_uwrap(self):
        """Creating an unwrapper shouldn't unwrap the message.

        Only iterating through the unwrapper should unwrap it.  We don't want to
        process the message at all until we're explicitly told to do so.

        """
        self.assertEqual(self.unwrapper.message, self.messages[-1])
        self.assertEqual(str(self.unwrapper).strip(), "")

    def test_iterator_unwraps_correctly(self):
        """The iterator should correctly unwrap each stage of the message."""

        unwrapped_messages = self.messages[:-1]

        for message in reversed(unwrapped_messages):
            self.assertEqual(message.strip(), self.unwrapper.next().strip())

    def test_no_header_invalid(self):
        """Messages without heads are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----BEGIN PGP SIGNED MESSAGE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_body_invalid(self):
        """Messages without bodies are considered invalid."""

        self.unwrapper.message = remove_line(self.unwrapper.message, "\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_footer_invalid(self):
        """Messages without feet are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----BEGIN PGP SIGNATURE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_end_invalid(self):
        """Messages without tails are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----END PGP SIGNATURE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)


if __name__ == "__main__":
    unittest.main()
