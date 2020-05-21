# SPDX-License-Identifier: AGPL-3.0-or-later

@essential @upgrades @system @backups
Feature: Software Upgrades
  Configure automatic software upgrades

Background:
  Given I'm a logged in user

Scenario: Enable automatic upgrades
  Given automatic upgrades are disabled
  When I enable automatic upgrades
  Then automatic upgrades should be enabled

Scenario: Backup and restore upgrades
  When I enable automatic upgrades
  And I create a backup of the upgrades app data
  And I disable automatic upgrades
  And I restore the upgrades app data backup
  Then automatic upgrades should be enabled

Scenario: Disable automatic upgrades
  Given automatic upgrades are enabled
  When I disable automatic upgrades
  Then automatic upgrades should be disabled
