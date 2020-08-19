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

Scenario: Set default permissions to List and read all files
  Given the bepasty application is enabled
  And I am not logged in to bepasty
  When I set the default permissions to List and read all files
  Then I should be able to List all Items in bepasty

Scenario: Set default permissions to Read files
  Given the bepasty application is enabled
  And I am not logged in to bepasty
  When I set the default permissions to Read files
  Then I should not be able to List all Items in bepasty

Scenario: Add password
  Given the bepasty application is enabled
  When I add a bepasty password
  Then I should be able to login to bepasty with that password

Scenario: Remove password
  Given the bepasty application is enabled
  When I add a bepasty password
  When I remove all bepasty passwords
  Then I should not be able to login to bepasty with that password

@backups
Scenario: Backup and restore bepasty
  Given the bepasty application is enabled
  When I add a bepasty password
  And I create a backup of the bepasty app data with name test_bepasty
  And I remove all bepasty passwords
  And I restore the bepasty app data backup with name test_bepasty
  Then the bepasty site should be available
  And I should be able to login to bepasty with that password

Scenario: Disable bepasty application
  Given the bepasty application is enabled
  When I disable the bepasty application
  Then the bepasty site should not be available
