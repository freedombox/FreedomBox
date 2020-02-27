# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @mldonkey @backups @sso
Feature: MLDonkey eDonkey Network Client
  Run the eDonkey Network client.

Background:
  Given I'm a logged in user
  Given the mldonkey application is installed

Scenario: Enable mldonkey application
  Given the mldonkey application is disabled
  When I enable the mldonkey application
  Then the mldonkey service should be running
  Then the mldonkey site should be available

Scenario: Upload an ed2k file to mldonkey
  Given the mldonkey application is enabled
  When all ed2k files are removed from mldonkey
  And I upload a sample ed2k file to mldonkey
  Then there should be 1 ed2k files listed in mldonkey

Scenario: Backup and restore mldonkey
  Given the mldonkey application is enabled
  When all ed2k files are removed from mldonkey
  And I upload a sample ed2k file to mldonkey
  And I create a backup of the mldonkey app data
  And all ed2k files are removed from mldonkey
  And I restore the mldonkey app data backup
  Then the mldonkey service should be running
  And there should be 1 ed2k files listed in mldonkey

Scenario: Disable mldonkey application
  Given the mldonkey application is enabled
  When I disable the mldonkey application
  Then the mldonkey service should not be running
  Then the mldonkey site should not be available
