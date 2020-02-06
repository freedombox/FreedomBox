# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @quassel @backups
Feature: Quassel IRC Client
  Run Quassel core.

Background:
  Given I'm a logged in user
  Given the quassel application is installed

Scenario: Enable quassel application
  Given the quassel application is disabled
  When I enable the quassel application
  Then the quassel service should be running

# TODO: Improve this to actually check that data configured servers is restored.
Scenario: Backup and restore quassel
  Given the quassel application is enabled
  When I create a backup of the quassel app data with name test_quassel
  And I restore the quassel app data backup with name test_quassel
  Then the quassel service should be running

Scenario: Disable quassel application
  Given the quassel application is enabled
  When I disable the quassel application
  Then the quassel service should not be running
