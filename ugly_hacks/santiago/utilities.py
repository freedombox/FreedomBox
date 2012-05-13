"""Shared utilities.

Currently contains a bunch of errors and config-file shortcuts.

"""

import ConfigParser as configparser


def load_config(configfile="test.cfg"):
    """Returns data from the named config file."""

    config = configparser.ConfigParser(
        {"KEYID":
             "D95C32042EE54FFDB25EC3489F2733F40928D23A"})
    config.read([configfile])
    return config

def multi_sign(message="hi", iterations=3, keyid=None, gpg=None):
    """Sign a message several times with a specified key."""

    messages = [message]

    if not gpg:
        gpg = gnupg.GPG(use_agent = True)
    if not keyid:
        keyid = load_config().get("pgpprocessor", "keyid")

    for i in range(iterations):
        messages.append(str(gpg.sign(messages[i], keyid=keyid)))

    return messages


class SignatureError(Exception):
    """Base class for signature-related errors."""

    pass

class InvalidSignatureError(SignatureError):
    """The signature in this message is cryptographically invalid."""
    
    pass

class UnwillingHostError(SignatureError):
    """The current process isn't willing to host a service for the client."""

    pass
