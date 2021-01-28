# SPDX-License-Identifier: AGPL-3.0-or-later

@backups @system
Feature: Backups module
  Create and restore backups.

Background:
  Given I'm a logged in user
  Given the bind application is installed

Scenario: Browser waits for redirect after restoring a backup
  Given the bind application is enabled
  When I create a backup of the bind app data with name test_backups
  And I restore the bind app data backup with name test_backups
  And I open the main page
  And I wait for 5 seconds
  Then the main page should be shown

Scenario: Download, upload and restore a backup
  Given the bind application is enabled
  When I set bind forwarders to 1.1.1.1
  And I create a backup of the bind app data with name test_backups
  And I set bind forwarders to 1.0.0.1
  And I download the app data backup with name test_backups
  And I restore the downloaded app data backup
  Then bind forwarders should be 1.1.1.1

Scenario: Set a schedule for a repository
  Given the backup schedule is set to disable for 1 daily, 2 weekly and 3 monthly at 2:00 without app names
  When I set the backup schedule to enable for 10 daily, 20 weekly and 30 monthly at 15:00 without app firewall
  Then the schedule should be set to enable for 10 daily, 20 weekly and 30 monthly at 15:00 without app firewall
