# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @syncthing @sso @backups
Feature: Syncthing File Synchronization
  Run Syncthing File Synchronization server.

Background:
  Given I'm a logged in user
  Given the syncthing application is installed

Scenario: Enable syncthing application
  Given the syncthing application is disabled
  When I enable the syncthing application
  Then the syncthing service should be running

Scenario: Add a syncthing folder
  Given the syncthing application is enabled
  And syncthing folder Test is not present
  When I add a folder /tmp as syncthing folder Test
  Then syncthing folder Test should be present

Scenario: Remove a syncthing folder
  Given the syncthing application is enabled
  And folder /tmp is present as syncthing folder Test
  When I remove syncthing folder Test
  Then syncthing folder Test should not be present

Scenario: Backup and restore syncthing
  Given the syncthing application is enabled
  And syncthing folder Test is not present
  When I add a folder /tmp as syncthing folder Test
  And I create a backup of the syncthing app data with name test_syncthing
  And I remove syncthing folder Test
  And I restore the syncthing app data backup with name test_syncthing
  Then syncthing folder Test should be present

Scenario: Disable syncthing application
  Given the syncthing application is enabled
  When I disable the syncthing application
  Then the syncthing service should not be running
