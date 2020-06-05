# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @ikiwiki
Feature: ikiwiki Wiki and Blog
  Manage wikis and blogs.

Background:
  Given I'm a logged in user
  Given the ikiwiki application is installed

Scenario: Enable ikiwiki application
  Given the ikiwiki application is disabled
  When I enable the ikiwiki application
  Then the ikiwiki site should be available

@backups
Scenario: Backup and restore ikiwiki
  Given the ikiwiki application is enabled
  When there is an ikiwiki wiki
  And I create a backup of the ikiwiki app data with name test_ikiwiki
  And I delete the ikiwiki wiki
  And I restore the ikiwiki app data backup with name test_ikiwiki
  Then the ikiwiki wiki should be restored

Scenario: Disable ikiwiki application
  Given the ikiwiki application is enabled
  When I disable the ikiwiki application
  Then the ikiwiki site should not be available
