# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @monkeysphere
Feature: Monkeysphere
  Import and publish OpenPGP keys for SSH and HTTPS keys

Background:
  Given I'm a logged in user
  And advanced mode is on
  And the monkeysphere application is installed
  And the domain name is set to mydomain.example

Scenario: Import SSH keys
  When I import SSH key for mydomain.example in monkeysphere
  Then the SSH key should imported for mydomain.example in monkeysphere

Scenario: Import HTTPS keys
  When I import HTTPS key for mydomain.example in monkeysphere
  Then the HTTPS key should imported for mydomain.example in monkeysphere

Scenario: Publish SSH keys
  Given the SSH key for mydomain.example is imported in monkeysphere
  Then I should be able to publish SSH key for mydomain.example in monkeysphere

Scenario: Publish HTTPS keys
  Given the HTTPS key for mydomain.example is imported in monkeysphere
  Then I should be able to publish HTTPS key for mydomain.example in monkeysphere

@backups
Scenario: Backup and restore monkeysphere
  When I import SSH key for mydomain.example in monkeysphere
  And I import HTTPS key for mydomain.example in monkeysphere
  And I create a backup of the monkeysphere app data with name test_monkeysphere
  And I restore the monkeysphere app data backup with name test_monkeysphere
  Then the SSH key should imported for mydomain.example in monkeysphere
  And the HTTPS key should imported for mydomain.example in monkeysphere
