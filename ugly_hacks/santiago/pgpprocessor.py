"""PGP message processing utilities.

Right now, this includes the Unwrapper, wihch unwraps and verifies each layer of
an onion-wrapped PGP message.

FIXME: replace this with a real library.  Why doesn't gnupg do this?

"""
from errors import InvalidSignatureError
import gnupg
import re


class Unwrapper(object):
    """Removes one layer of PGP message header and footer per iteration.

    Good for singly- or multiply-wrapped messages.

    After a single iteration, the original message is available in
    ``original_message`` while the message's contents are in
    ``str(Unwrapper)``.

    Sucessive iterations unwrap additional layers of the message.  Good for
    onion-signed or -encrypted messages.

    Using it is pretty darn simple.  The following both creates and unwraps a
    signed message::

    >>> gpg = gnupg.GPG(use_agent = True)
    >>> message = "hi"
    >>> signed_message = str(gpg.sign(message, keyid = "0928D23A"))
    >>> unwrapper = pgpprocessor.Unwrapper(signed_message)
    >>> [message == x.strip() for x in unwrapper]
    [True]

    """
    START, HEAD, BODY, FOOTER, END = "start", "header", "body", "footer", "end"

    TYPES = (SIG, CRYPT) = "sig", "crypt"

    SIG_LINES = (SIG_HEAD, SIG_BODY, SIG_FOOTER, SIG_END) = (
        "-----BEGIN PGP SIGNED MESSAGE-----\n",
        "\n",
        "-----BEGIN PGP SIGNATURE-----\n",
        "-----END PGP SIGNATURE-----\n")

    CRYPT_LINES = (CRYPT_HEAD, CRYPT_END) = ("-----BEGIN PGP MESSAGE-----\n",
                                             "-----END PGP MESSAGE-----\n")

    # ^- - - (-----SOMETHING-----|-----OTHERTHING-----)$
    _TARGET = "^(- )+({0})$"
    SIG_TARGET = re.compile(_TARGET.format("|".join(SIG_LINES)))
    CRYPT_TARGET = re.compile(_TARGET.format("|".join(CRYPT_LINES)))

    def __init__(self, message, gpg = None,
                 gnupg_new = None, gnupg_verify = None, gnupg_decrypt = None):
        """Prepare to unwrap a PGP message.

        If a gnupg.GPG instance isn't passed in as the ``gpg`` parameter, it's
        created during instantiation with the ``gnupg_new`` keyword arguments.

        The ``_verify`` and ``_decrypt`` arguments are used when verifying
        signatures and decrypting messages, respectively.

        post::

            self.gpg # exists
            self.gpg_data # exists

        """
        if gnupg_new == None:
            gnupg_new = dict()
        if gnupg_verify == None:
            gnupg_verify = dict()
        if gnupg_decrypt == None:
            gnupg_decrypt = dict()
        if gpg == None:
            gpg = gnupg.GPG(**gnupg_new)

        self.message = message
        self.gnupg_verify = gnupg_verify
        self.gnupg_decrypt = gnupg_decrypt
        self.type = ""
        self.gpg = gpg
        self.gpg_data = None
        self.reset_fields()

    def reset_fields(self):
        """Removes all extracted data from the iterator.

        This resets it to a new or clean state, ready for the next iteration.

        post::

            True not in map((self.start, self.header, self.body, self.footer,
                             self.end, self.gpg_data), bool)

        """
        self.start = list()
        self.header = list()
        self.body = list()
        self.footer = list()
        self.end = list()
        self.gpg_data = None

    def __iter__(self):
        return self

    def next(self):
        """Remove one layer of PGP message wrapping.

        Return the message's contents, and set self.body as the message's body.
        Also, set the message's header and footer in self, respectively.

        Raise an InvalidSignature Error if signature isn't valid.

        This is a simple state-machine: certain lines advance the state of the
        machine, and until the machine is advanced again, all lines are added to
        that part of the message.  When we reach the end of the message, the
        state machine is reset, but starts with the message it just unwrapped.

        It has one quirk in two states: the head -> body and footer -> end
        transitions append their lines to the former state and then change
        state, unlike all the other transitions which change state first.
        Messages would be built non-intuitively without those exceptions.

        """
        point = Unwrapper.START
        msg_type = ""

        self.reset_fields()

        for line in self.message.splitlines(True):
            if point == Unwrapper.START and line == Unwrapper.SIG_HEAD:
                point = Unwrapper.HEAD
                msg_type = Unwrapper.SIG
            elif point == Unwrapper.START and line == Unwrapper.CRYPT_HEAD:
                point = Unwrapper.HEAD
                msg_type = Unwrapper.CRYPT
            elif point == Unwrapper.HEAD and line == Unwrapper.SIG_BODY:
                point = Unwrapper.BODY
            elif (point == Unwrapper.BODY and line == Unwrapper.SIG_FOOTER and
                  msg_type == Unwrapper.SIG):
                point = Unwrapper.FOOTER
            elif ((point == Unwrapper.FOOTER and line == Unwrapper.SIG_END
                   and msg_type == Unwrapper.SIG)
                  or (point == Unwrapper.BODY and line == Unwrapper.CRYPT_END
                      and msg_type == Unwrapper.CRYPT)):
                # add the footer line to the footer, not the post-script
                self.footer.append(line)
                point = Unwrapper.END
                continue

            getattr(self, point).append(line)

        self.handle_end_conditions(point, msg_type)

        self.type = msg_type
        self.message = "".join(Unwrapper.unwrap(self.body, self.type)).lstrip()

        return self.gpg_data

    def handle_end_conditions(self, point, msg_type):
        """Handle end-conditions of message.

        Do the right thing based on the state machine's results.  If there is no
        PGP data in the message, raise a StopIteration error.

        # pre::
        #
        #     msg_type in (Unwrapper.CRYPT, Unwrapper.SIG)
        #     point == Unwrapper.END

        """
        if point != Unwrapper.END or msg_type not in (Unwrapper.CRYPT,
                                                      Unwrapper.SIG):
            raise StopIteration("No valid PGP data.")

        args = (self.gnupg_verify if msg_type == Unwrapper.SIG
                else self.gnupg_decrypt)

        self.gpg_data = {
            Unwrapper.SIG: self.gpg.verify,
            Unwrapper.CRYPT: self.gpg.decrypt
            }[msg_type](str(self), **args)

        if not (self.gpg_data and self.gpg_data.valid):
            raise InvalidSignatureError()

    def __str__(self):
        """Returns the original GPG-data in the unwrapped message.

        Non-PGP-message data (before and after the message) are not returned.

        """
        return "".join([
                "".join(x) for x in (self.header, self.body, self.footer) ])

    @classmethod
    def unwrap(cls, message, msg_type):
        """

        pre::

            msg_type in (Unwrapper.SIG, Unwrapper.CRYPT)

        """
        if msg_type == Unwrapper.SIG:
            target = Unwrapper.SIG_TARGET
        elif msg_type == Unwrapper.CRYPT:
            target = Unwrapper.CRYPT_TARGET
        else:
            raise ValueError("Type must be one of: {0}".format(
                    ", ".join(Unwrapper.TYPES)))

        for i, line in enumerate(message):
            if target.match(line):
                message[i] = line[2:]

        return message


if __name__ == "__main__":
    import doctest
    doctest.testmod()
