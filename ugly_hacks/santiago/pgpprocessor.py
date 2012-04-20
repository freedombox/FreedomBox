"""PGP message processing utilities."""

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

    TYPES = (SIG, CRYPT) = "sig", "crypt"

    SIG_LINES = (SIG_HEAD, SIG_BODY, SIG_FOOTER, SIG_END) = (
            "-----BEGIN PGP SIGNED MESSAGE-----",
            "",
            "-----BEGIN PGP SIGNATURE-----",
            "-----END PGP SIGNATURE-----")

    CRYPT_LINES = (CRYPT_HEAD, CRYPT_END) = ("-----BEGIN PGP MESSAGE-----",
                                             "-----END PGP MESSAGE-----")

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

        This is a really simple state-machine: certain lines advance the state
        of the machine, and until the machine is advanced again, all lines are
        added to that part of the message.  When we reach the end of the
        message, the state machine is reset, but starts with the message it just
        unwrapped.

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

        # TODO figure this out.
        self.gpg_data = {
            PgpUnwrapper.SIG: self.gpg.verify,
            PgpUnwrapper.CRYPT: self.gpg.decrypt
        }[type_](str(self), **args)

        self.type = type_
        self.body = PgpUnwrapper.unwrap(self.body)

        # reset the state machine, now that we've unwrapped a layer.
        self.message = "\n".join(self.body)

        if not data:
            raise InvalidSignatureError()

    @classmethod
    def unwrap(cls, message, type_):
        """

        pre::

            type_ in (PgpUnwrapper.SIG, PgpUnwrapper.CRYPT)

        """
        if type_ == PgpUnwrapper.SIG:
            lines = PgpUnwrapper.SIG_LINES
        elif type_ == PgpUnwrapper.CRYPT:
            lines = PgpUnwrapper.CRYPT_LINES
        else:
            raise ValueError("Type must be one of: {0}".format(
                    ", ".join(PgpUnwrapper.TYPES)))

        # ^- - - (-----SOMETHING-----|-----OTHERTHING-----)$
        target = re.compile("^(- )+({0})$".format("|".join(lines)))


        for line in message:
            if target.match(line):
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
