# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @ikiwiki
Feature: ikiwiki Wiki and Blog
  Manage wikis and blogs.

Background:
  Given I'm a logged in user
  Given the wiki application is installed

Scenario: Enable wiki application
  Given the wiki application is disabled
  When I enable the wiki application
  Then the wiki site should be available

@backups
Scenario: Backup and restore wiki
  Given the wiki application is enabled
  When there is an ikiwiki wiki
  And I create a backup of the ikiwiki app data with name test_ikiwiki
  And I delete the ikiwiki wiki
  And I restore the ikiwiki app data backup with name test_ikiwiki
  Then the ikiwiki wiki should be restored

Scenario: Disable wiki application
  Given the wiki application is enabled
  When I disable the wiki application
  Then the wiki site should not be available
