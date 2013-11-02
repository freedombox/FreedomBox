#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

import user_store
from logger import Logger
import cfg
import unittest
import cherrypy
import plugin_mount
import os
from model import User
cfg.log = Logger()

cherrypy.log.access_file = None

class UserStore(unittest.TestCase):
    """Test each function of user_store to confirm they work as expected"""

    def setUp(self):
        cfg.user_db = os.path.join(cfg.file_root, "tests/testdata/users");
        self.userstore = plugin_mount.UserStoreModule.get_plugins()[0]

    def tearDown(self):
        for user in self.userstore.get_all():
            self.userstore.remove(user[0])
        self.userstore.close()
        
    def test_user_does_not_exist(self):
        self.assertEqual(self.userstore.exists("notausername"),False)

    def test_user_does_exist(self):
        self.add_user("isausername", False)
        self.assertEqual(self.userstore.exists("isausername"),True)

    def test_add_user(self):
        self.assertEqual(len(self.userstore.items()),0)
        self.add_user("test_user", False)
        self.assertEqual(len(self.userstore.items()),1)

    def test_user_is_in_expert_group(self):
        self.add_user("test_user", True)
        self.assertEqual(self.userstore.expert("test_user"),True)

    def test_user_is_not_in_expert_group(self):
        self.add_user("test_user", False)
        self.assertEqual(self.userstore.expert("test_user"),False)

    def test_user_removal(self):
        self.assertEqual(len(self.userstore.items()),0)
        self.add_user("test_user", False)
        self.assertEqual(len(self.userstore.items()),1)
        self.userstore.remove("test_user")
        self.assertEqual(len(self.userstore.items()),0)

    def test_get_user_email_attribute(self):
        self.add_user("test_user", False,"test@home")
        self.assertEqual(self.userstore.attr("test_user","email"),"test@home")

    def test_get_user(self):
        test_user = self.add_user("test_user", False)
        self.assertEqual(self.userstore.get("test_user"),test_user)

    def test_get_all_users(self):
        self.add_user("test_user1", False)
        self.add_user("test_user2", False)
        self.assertEqual(len(self.userstore.get_all()),2)

    def add_user(self, test_username, add_to_expert_group, email=''):
        test_user = self.create_user(test_username, email)
        if add_to_expert_group:
            test_user = self.add_user_to_expert_group(test_user)
        self.userstore.set(test_username,test_user)
        return test_user

    def create_user(self, username, email=''):
        test_user = User()
        test_user["username"] = username
        test_user["email"] = email
        return test_user

    def add_user_to_expert_group(self, user):
        user["groups"] = ["expert"]
        return user

if __name__ == "__main__":
    unittest.main()