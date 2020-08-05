# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @bepasty
Feature: bepasty File Sharing
  Run bepasty file upload and sharing app.

Background:
  Given I'm a logged in user
  Given the bepasty application is installed

Scenario: Enable bepasty application
  Given the bepasty application is disabled
  When I enable the bepasty application
  Then the bepasty site should be available

Scenario: Add password
  Given the bepasty application is enabled
  When I add a password
  Then I should be able to login to bepasty with that password

Scenario: Remove password
  Given the bepasty application is enabled
  When I remove all passwords
  Then I should not be able to login to bepasty with that password

@backups
Scenario: Backup and restore bepasty
  Given the bepasty application is enabled
  When I add a password
  And I create a backup of the bepasty app data with name test_bepasty
  And I remove all passwords
  And I restore the bepasty app data backup with name test_bepasty
  Then the bepasty site should be available
  And I should be able to login to bepasty with that password

Scenario: Disable bepasty application
  Given the bepasty application is enabled
  When I disable the bepasty application
  Then the bepasty site should not be available
