# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @privoxy @backups
Feature: Privoxy Web Proxy
  Proxy web connections for enhanced privacy.

Background:
  Given I'm a logged in user
  Given the privoxy application is installed

Scenario: Enable privoxy application
  Given the privoxy application is disabled
  When I enable the privoxy application
  Then the privoxy service should be running

Scenario: Backup and restore privoxy
  Given the privoxy application is enabled
  When I create a backup of the privoxy app data
  And I restore the privoxy app data backup
  Then the privoxy service should be running

Scenario: Disable privoxy application
  Given the privoxy application is enabled
  When I disable the privoxy application
  Then the privoxy service should not be running
