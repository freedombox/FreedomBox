# SPDX-License-Identifier: AGPL-3.0-or-later

@essential @upgrades @system
Feature: Software Upgrades
  Configure automatic software upgrades

Background:
  Given I'm a logged in user

Scenario: Enable automatic upgrades
  Given automatic upgrades are disabled
  When I enable automatic upgrades
  Then automatic upgrades should be enabled

@backups
Scenario: Backup and restore upgrades
  When I enable automatic upgrades
  And I create a backup of the upgrades app data with name test_upgrades
  And I disable automatic upgrades
  And I restore the upgrades app data backup with name test_upgrades
  Then automatic upgrades should be enabled

Scenario: Disable automatic upgrades
  Given automatic upgrades are enabled
  When I disable automatic upgrades
  Then automatic upgrades should be disabled
