# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @zoph
Feature: Zoph Organises PHotos
  Run photo organiser

Background:
  Given I'm a logged in user
  Given the zoph application is installed
  Given the zoph application is setup

Scenario: Enable zoph application
  Given the zoph application is disabled
  When I enable the zoph application
  Then the zoph application is enabled

@backups
Scenario: Backup and restore zoph
  Given the zoph application is enabled
  When I create a backup of the zoph app data with name test_zoph
  And I restore the zoph app data backup with name test_zoph
  Then the zoph application is enabled

Scenario: Disable zoph application
  Given the zoph application is enabled
  When I disable the zoph application
  Then the zoph application is disabled
