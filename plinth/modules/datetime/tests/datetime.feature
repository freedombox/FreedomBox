# SPDX-License-Identifier: AGPL-3.0-or-later

@essential @datetime @system
Feature: Date and Time
  Configure time zone and network time service.

Background:
  Given I'm a logged in user

Scenario: Disable network time application
  Given the datetime application can be disabled
  And the datetime application is enabled
  When I disable the datetime application
  Then the datetime service should not be running

Scenario: Enable network time application
  Given the datetime application can be disabled
  And the datetime application is disabled
  When I enable the datetime application
  Then the datetime service should be running

Scenario: Set timezone
  When I set the time zone to Africa/Abidjan
  Then the time zone should be Africa/Abidjan

@backups
Scenario: Backup and restore datetime
  When I set the time zone to Africa/Accra
  And I create a backup of the datetime app data with name test_datetime
  And I set the time zone to Africa/Cairo
  And I restore the datetime app data backup with name test_datetime
  Then the time zone should be Africa/Accra
