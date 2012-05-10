class SignatureError(Exception):
    """Base class for signature-related errors."""

    pass

class InvalidSignatureError(SignatureError):
    """The signature in this message is cryptographically invalid."""
    
    pass

class UnwillingHostError(SignatureError):
    """The current process isn't willing to host a service for the client."""

    pass
