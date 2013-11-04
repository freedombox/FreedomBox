#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

import user_store, auth
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

    def test_add_user(self):
        self.assertIsNone(auth.add_user("test_user", "password"))
        self.assertIsNotNone(auth.add_user(None, "password"))
        self.assertIsNotNone(auth.add_user("test_user", None))
        self.assertIsNotNone(auth.add_user("test_user", "password"))

    def test_password_check(self):
        auth.add_user("test_user", "password")

        # check_credentials returns None if there is no error,
        # or returns error string
        self.assertIsNone(auth.check_credentials("test_user", "password"))
        self.assertIsNotNone(auth.check_credentials("test_user", "wrong"))

    def test_nonexistent_user(self):
        self.assertIsNotNone(auth.check_credentials("test_user", "password"))

    def test_password_too_long(self):
        password = "x" * 4097
        self.assertIsNotNone(auth.add_user("test_user", password))
        self.assertIsNotNone(auth.check_credentials("test_user", password))

    def test_salt_is_random(self):
        auth.add_user("test_user1", "password")
        auth.add_user("test_user2", "password")
        self.assertNotEqual(
            cfg.users["test_user1"]["salt"],
            cfg.users["test_user2"]["salt"]
            )

    def test_hash_is_random(self):
        auth.add_user("test_user1", "password")
        auth.add_user("test_user2", "password")
        self.assertNotEqual(
            cfg.users["test_user1"]["passphrase"],
            cfg.users["test_user2"]["passphrase"]
            )

if __name__ == "__main__":
    unittest.main()
