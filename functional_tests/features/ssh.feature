# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @ssh @backups
Feature: Secure Shell Server
  Run secure shell server.

Background:
  Given I'm a logged in user
  Given the ssh application is installed

Scenario: Enable ssh application
  Given the ssh application is disabled
  When I enable the ssh application
  Then the ssh service should be running

Scenario: Disable ssh application
  Given the ssh application is enabled
  When I disable the ssh application
  Then the ssh service should not be running

# TODO: Improve this to actually check that earlier ssh certificate has been
# restored.
Scenario: Backup and restore ssh
  Given the ssh application is enabled
  When I create a backup of the ssh app data
  And I restore the ssh app data backup
  Then the ssh service should be running
