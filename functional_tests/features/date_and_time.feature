# SPDX-License-Identifier: AGPL-3.0-or-later

@essential @date_and_time @system @backups
Feature: Date and Time
  Configure time zone and network time service.

Background:
  Given I'm a logged in user

Scenario: Disable network time application
  Given the network time application can be disabled
  And the network time application is enabled
  When I disable the network time application
  Then the network time service should not be running

Scenario: Enable network time application
  Given the network time application can be disabled
  And the network time application is disabled
  When I enable the network time application
  Then the network time service should be running

Scenario: Set timezone
  When I set the time zone to Africa/Abidjan
  Then the time zone should be Africa/Abidjan

Scenario: Backup and restore datetime
  When I set the time zone to Africa/Accra
  And I create a backup of the datetime app data
  And I set the time zone to Africa/Cairo
  And I restore the datetime app data backup
  Then the time zone should be Africa/Accra
