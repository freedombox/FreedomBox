"""PGP message processing utilities."""

from errors import InvalidSignatureError, UnwillingHostError
import gnupg
import re


class Unwrapper(object):
    """Removes one layer of PGP message header and footer per iteration.

    Good for singly- or multiply-wrapped messages.

    FIXME: replace with a real library for this.  Why doesn't gnupg do this?

    After a single iteration, the original message is available in
    ``original_message`` while the message's contents are in
    ``str(Unwrapper)``.

    Sucessive iterations unwrap additional layers of the message.  Good for
    onion-signed or -encrypted messages.

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

        if gnupg_new == None:
            gnupg_new = dict()
        if gnupg_verify == None:
            gnupg_verify = dict()
        if gnupg_decrypt == None:
            gnupg_decrypt = dict()
        if gpg == None:
            gpg = gnupg.GPG(**gnupg_new)

        self.message = message
        self.gnupg_new = gnupg_new
        self.gnupg_verify = gnupg_verify
        self.gnupg_decrypt = gnupg_decrypt
        self.type = ""
        self.gpg = gpg
        self.gpg_data = None
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
        type_ = ""

        self.reset_fields()

        for line in self.message.splitlines(True):
            if point == Unwrapper.START and line == Unwrapper.SIG_HEAD:
                point = Unwrapper.HEAD
                type_ = Unwrapper.SIG
            elif point == Unwrapper.START and line == Unwrapper.CRYPT_HEAD:
                point = Unwrapper.HEAD
                type_ = Unwrapper.CRYPT
            elif point == Unwrapper.HEAD and line == Unwrapper.SIG_BODY:
                point = Unwrapper.BODY
            elif (point == Unwrapper.BODY and line == Unwrapper.SIG_FOOTER and
                  type_ == Unwrapper.SIG):
                point = Unwrapper.FOOTER
            elif ((point == Unwrapper.FOOTER and line == Unwrapper.SIG_END
                   and type_ == Unwrapper.SIG)
                  or (point == Unwrapper.BODY and line == Unwrapper.CRYPT_END
                      and type_ == Unwrapper.CRYPT)):
                # add the footer line to the footer, not the post-script
                self.footer.append(line)
                point = Unwrapper.END
                continue

            getattr(self, point).append(line)

        self.handle_end_conditions(point, type_)

        return "".join(self.body)

    def handle_end_conditions(self, point, type_):
        """Handle end-conditions of message.

        Do the right thing based on the state machine's results.  If there is no
        PGP data in the message, raise a StopIteration error.

        """
        if point != Unwrapper.END or type_ not in (Unwrapper.CRYPT,
                                                   Unwrapper.SIG):
            raise StopIteration("No valid PGP data.")

        args = (self.gnupg_verify if type_ == Unwrapper.SIG
                else self.gnupg_decrypt)

        self.gpg_data = {
            Unwrapper.SIG: self.gpg.verify,
            Unwrapper.CRYPT: self.gpg.decrypt
            }[type_](str(self), **args)

        self.type = type_
        self.body = Unwrapper.unwrap(self.body, self.type)

        # reset the state machine, now that we've unwrapped a layer.
        self.message = "".join(self.body)

        if not (self.gpg_data and self.gpg_data.valid):
            raise InvalidSignatureError()

    @classmethod
    def unwrap(cls, message, type_):
        """

        pre::

            type_ in (Unwrapper.SIG, Unwrapper.CRYPT)

        """
        if type_ == Unwrapper.SIG:
            target = Unwrapper.SIG_TARGET
        elif type_ == Unwrapper.CRYPT:
            target = Unwrapper.CRYPT_TARGET
        else:
            raise ValueError("Type must be one of: {0}".format(
                    ", ".join(Unwrapper.TYPES)))

        for i, line in enumerate(message):
            if target.match(line):
                message[i] = line[2:]

        return message

    def __str__(self):
        """Returns the GPG-part of the current message.

        Non-PGP-message data (before and after the message) are not returned.

        """
        return "".join([
                "".join(x) for x in (self.header, self.body, self.footer) ])

    def original_message(self):
        """Returns the current wrapped message.

        It's an iterator, so previous iterations' data isn't available.

        """
        return "".join([
                "".join(x) for x in (self.start, self.header, self.body,
                                       self.footer, self.end) ])

if __name__ == "__main__":
    unittest.main()
