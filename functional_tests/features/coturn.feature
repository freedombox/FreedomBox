# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @coturn @backups
Feature: Coturn STUN/TURN Server
  Run the Coturn STUN/TURN server.

Background:
  Given I'm a logged in user
  And advanced mode is on
  And the coturn application is installed

Scenario: Enable coturn application
  Given the coturn application is disabled
  When I enable the coturn application
  Then the coturn service should be running

# TODO: Improve this by checking that secret and domain did not change
Scenario: Backup and restore coturn
  Given the coturn application is enabled
  When I create a backup of the coturn app data
  And I restore the coturn app data backup
  Then the coturn service should be running

Scenario: Disable coturn application
  Given the coturn application is enabled
  When I disable the coturn application
  Then the coturn service should not be running
