from pprint import pprint
import sys
sys.path.extend(["../..", ".",
                 "/home/nick/programs/python-gnupg/python-gnupg-0.2.9"])
import gnupg
import simplesantiago


# important variables.

key_id = ""
pass_phrase = ""
recipient = ""
gpg = gnupg.GPG(use_agent=True)

# utility functions

def show(name, item, iterations=1):
    print "#" * iterations, name
    if hasattr(item, "__dict__"):
        for k, v in item.__dict__.iteritems():
            show(k, v, iterations + 1)
    elif type(item) in (str, unicode):
        print item
    else:
        pprint(item)

# basic data printing tests.

def encrypted_test(data):
    global key_id, pass_phrase, gpg

    encrypted_data = gpg.encrypt(data, recipient, passphrase=pass_phrase)
    encrypted_string = str(encrypted_data)
    encrypted(encrypted_data, encrypted_string, data)

def encrypted(encrypted_data, encrypted_string, unencrypted_string):
    """Print out some basic important items."""

    print "encrypted data!"
    print 'ok: ', encrypted_data.ok
    print 'status: ', encrypted_data.status
    print 'stderr: ', encrypted_data.stderr
    print 'unencrypted_string: ', unencrypted_string
    print 'encrypted_string: ', encrypted_string
    show("encrypted_data", encrypted_data)

def decrypted_test(encrypted_string):
    global key_id, pass_phrase, gpg

    decrypted_data = gpg.decrypt(encrypted_string, passphrase=pass_phrase)
    decrypted_data = gpg.decrypt(encrypted_string)
    decrypted(decrypted_data)

def decrypted(decrypted_data):
    """Print out some basic important items."""

    print "decrypted data!"
    print 'ok: ', decrypted_data.ok
    print 'status: ', decrypted_data.status
    print 'stderr: ', decrypted_data.stderr
    print 'decrypted string: ', decrypted_data.data
    show("decrypted_data", decrypted_data)

# interactive, value-returning tests

def sign_test(message):
    signed = gpg.sign(message)
    show("signed", signed)
    return signed

def signcrypt_test(data):
    global key_id, pass_phrase, gpg

    encrypted_data = gpg.encrypt(data, recipient, passphrase=pass_phrase)
    return encrypted_data

def example_test():
    """Almost directly out of the Python-Gnupg docs."""

    gpg = gnupg.GPG(gnupghome="keys")
    show("gpg", gpg)
    input_ = gpg.gen_key_input(passphrase='foo')
    show("input_", input_)
    result = gpg.gen_key(input_)
    show("result", result)
    print1 = result.fingerprint
    show("print1", print1)
    input_ = gpg.gen_key_input()
    show("input_", input_)
    result = gpg.gen_key(input_)
    show("result", result)
    print2 = result.fingerprint
    show("print2", print2)
    result = gpg.encrypt("hello",print2)
    show("result", result)
    message = str(result)
    show("message", message)
    return message

def verify_test(message):
    """The two important results of the verify method are valid and fingerprint.

    """
    verify = gpg.verify(str(message))
    show("verify", verify)
    # show(verify.valid)
    # show(verify.fingerprint)
    return verify

def unwrapper_test(data):
    """Does the PgpUnwrapper do its job?"""
    global key_id, pass_phrase, gpg

    # create a new key if we don't have one.
    if not key_id:
        key_id = None

        gpg = gnupg.GPG(gnupghome="keys", useagent=True)

        print "key input..."
        input_ = gpg.gen_key_input(key_length = 1, passphrase=pass_phrase)
        print "key..."
        result = gpg.gen_key(input_)

    # first signing

    print "sign..."
    data = gpg.sign(data, keyid=key_id)
    # believe it or not, this is transformative.
    data = str(data)
    print "data:\n", data, "\n:data"

    # second signing

    data = gpg.sign(data, keyid=key_id)
    data = str(data)
    print "data:\n", data, "\n:data"

    # unwrap it!

    dog = simplesantiago.PgpUnwrapper(str(data))

    print "unwrapping..."
    for message in dog:
        print "type:", dog.type
        print "message:", message


if __name__ == "__main__":
    """Below, each set of lines is a set of tests:

    1. encrypted_test, decrypted_test
    2. example_test
    3. signcrypt_test
    4. sign_test, verify_test
    5. unwrapper_test

    """
    key_id = "D95C32042EE54FFDB25EC3489F2733F40928D23A"
    recipient = "nick.m.daly@gmail.com"

    data = {'lol': 'cats'}

    # encrypted_data = encrypted_test(str(data))
    # decrypted_test(str(encrypted_data))

    # example_test()

    # crypt_data = signcrypt_test(str(data))

    # signed = sign_test(str(data))
    # verify = verify_test(signed)

    unwrapper_test(str(data))
