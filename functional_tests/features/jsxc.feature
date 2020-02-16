# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @jsxc @backups
Feature: JSXC XMPP Client
  Run the JSXC XMPP client.

Background:
  Given I'm a logged in user

Scenario: Install jsxc application
  Given the jsxc application is installed
  Then the jsxc site should be available

Scenario: Backup and restore jsxc
  Given the jsxc application is installed
  When I create a backup of the jsxc app data
  And I restore the jsxc app data backup
  Then the jsxc site should be available
