# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @dynamicdns @backups
Feature: Dynamic DNS Client
  Update public IP to a GnuDIP server.

Background:
  Given I'm a logged in user
  And the dynamicdns application is installed

Scenario: Backup and restore configuration
  Given dynamicdns is configured
  When I create a backup of the dynamicdns app data
  And I change the dynamicdns configuration
  And I restore the dynamicdns app data backup
  Then dynamicdns should have the original configuration
