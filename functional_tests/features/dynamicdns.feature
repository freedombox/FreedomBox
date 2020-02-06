# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @dynamicdns
Feature: Dynamic DNS Client
  Update public IP to a GnuDIP server.

Background:
  Given I'm a logged in user
  And the dynamicdns application is installed

@backups
Scenario: Backup and restore configuration
  Given dynamicdns is configured
  When I create a backup of the dynamicdns app data with name test_dynamicdns
  And I change the dynamicdns configuration
  And I restore the dynamicdns app data backup with name test_dynamicdns
  Then dynamicdns should have the original configuration
