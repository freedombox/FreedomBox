# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @searx @backups @sso
Feature: Searx Web Search
  Run Searx metasearch engine.

Background:
  Given I'm a logged in user
  Given the searx application is installed

Scenario: Enable searx application
  Given the searx application is disabled
  When I enable the searx application
  Then the searx site should be available

Scenario: Backup and restore searx
  Given the searx application is enabled
  When I create a backup of the searx app data
  And I restore the searx app data backup
  Then the searx site should be available

Scenario: Disable searx application
  Given the searx application is enabled
  When I disable the searx application
  Then the searx site should not be available

Scenario: Enable public access
  Given the searx application is enabled
  When I enable public access in searx
  And I log out
  Then searx app should be visible on the front page
  And the searx site should be available

Scenario: Disable public access
  Given the searx application is enabled
  When I disable public access in searx
  And I log out
  Then searx app should not be visible on the front page
  And the searx site should not be available

Scenario: Preserve public access setting
  Given the searx application is enabled
  And public access is enabled in searx
  When I disable the searx application
  And I enable the searx application
  And I log out
  Then searx app should be visible on the front page
  And the searx site should be available

