#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

import user_store, auth
from passlib.hash import bcrypt
from logger import Logger
import cfg
import unittest
import cherrypy
import plugin_mount
import os
from model import User
cfg.log = Logger()

cherrypy.log.access_file = None

class Auth(unittest.TestCase):
    """Test check_credentials function of auth to confirm it works as expected"""

    def setUp(self):
        cfg.user_db = os.path.join(cfg.file_root, "tests/testdata/users");
        cfg.users = plugin_mount.UserStoreModule.get_plugins()[0]

    def tearDown(self):
        for user in cfg.users.get_all():
            cfg.users.remove(user[0])
        cfg.users.close()

    def test_password_check(self):
        self.add_user("test_user", "password")

        # check_credentials returns None if there is no error, or returns error string
        self.assertIsNone(auth.check_credentials("test_user", "password"))
        self.assertIsNotNone(auth.check_credentials("test_user", "wrong"))

    def test_salt_check(self):
        test_user = self.add_user("test_user", "password", "abcdefghijklmnopqrstuv")
        self.assertIsNotNone(auth.check_credentials("test_user", "password"))

    def test_salt_is_random(self):
        test_user1 = self.add_user("test_user1", "password")
        test_user2 = self.add_user("test_user2", "password")
        self.assertNotEqual(test_user1["salt"], test_user2["salt"])

    def test_hash_is_random(self):
        test_user1 = self.add_user("test_user1", "password")
        test_user2 = self.add_user("test_user2", "password")
        self.assertNotEqual(test_user1["passphrase"], test_user2["passphrase"])

    # set fake_salt if you want to store an invalid salt
    def add_user(self, test_username, passphrase='', fake_salt=None):
        test_user = self.create_user(test_username, passphrase, fake_salt)
        cfg.users.set(test_username,test_user)
        return test_user

    def create_user(self, username, passphrase='', fake_salt=None):
        test_user = User()
        test_user["username"] = username
        pass_hash = bcrypt.encrypt(passphrase)
        test_user["passphrase"] = pass_hash
        if fake_salt:
            test_user["salt"] = fake_salt
        else:
            # for bcrypt, the salt is output as part of the hash
            test_user["salt"] = pass_hash[7:29]

        return test_user

if __name__ == "__main__":
    unittest.main()
