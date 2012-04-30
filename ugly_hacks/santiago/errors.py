class SignatureError(Exception):
    pass

class InvalidSignatureError(SignatureError):
    pass

class UnwillingHostError(SignatureError):
    pass
