class User(dict):
    """ Every user must have keys for a username, name, passphrase (this
    is a bcrypt hash of the password), salt, groups, and an email address.
    They can be blank or None, but the keys must exist. """
    def __init__(self, dict=None):
        for key in ['username', 'name', 'passphrase', 'salt', 'email']:
            self[key] = ''
        for key in ['groups']:
            self[key] = []
        if dict:
            for key in dict:
                self[key] = dict[key]

    def __getattr__(self, attr):
        return None
