# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @mumble @backups
Feature: Mumble Voice Chat
  Run Mumble voice chat server.

Background:
  Given I'm a logged in user
  Given the mumble application is installed

Scenario: Enable mumble application
  Given the mumble application is disabled
  When I enable the mumble application
  Then the mumble service should be running

# TODO: Improve this to actually check that data such as rooms, identity or
# certificates are restored.
Scenario: Backup and restore mumble
  Given the mumble application is enabled
  When I create a backup of the mumble app data with name test_mumble
  And I restore the mumble app data backup with name test_mumble
  Then the mumble service should be running

Scenario: Disable mumble application
  Given the mumble application is enabled
  When I disable the mumble application
  Then the mumble service should not be running
