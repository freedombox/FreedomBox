# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @coquelicot @backups @skip
Feature: Coquelicot File Sharing
  Run Coquelicot File Sharing server.

Background:
  Given I'm a logged in user
  Given the coquelicot application is installed

Scenario: Enable coquelicot application
  Given the coquelicot application is disabled
  When I enable the coquelicot application
  Then the coquelicot service should be running

Scenario: Modify maximum upload size
  Given the coquelicot application is enabled
  When I modify the maximum file size of coquelicot to 256
  Then the maximum file size of coquelicot should be 256

Scenario: Modify upload password
  Given the coquelicot application is enabled
  When I modify the coquelicot upload password to whatever123
  Then I should be able to login to coquelicot with password whatever123

Scenario: Modify maximum upload size in disabled case
  Given the coquelicot application is disabled
  When I modify the maximum file size of coquelicot to 123
  Then the coquelicot service should not be running

Scenario: Upload a file to coquelicot
  Given the coquelicot application is enabled
  And a sample local file
  When I modify the coquelicot upload password to whatever123
  And I upload the sample local file to coquelicot with password whatever123
  And I download the uploaded file from coquelicot
  Then contents of downloaded sample file should be same as sample local file

Scenario: Backup and restore coquelicot
  Given the coquelicot application is enabled
  When I modify the coquelicot upload password to beforebackup123
  And I modify the maximum file size of coquelicot to 128
  And I upload the sample local file to coquelicot with password beforebackup123
  And I create a backup of the coquelicot app data with name test_coquelicot
  And I modify the coquelicot upload password to afterbackup123
  And I modify the maximum file size of coquelicot to 64
  And I restore the coquelicot app data backup with name test_coquelicot
  And I download the uploaded file from coquelicot
  Then the coquelicot service should be running
  And I should be able to login to coquelicot with password beforebackup123
  And the maximum file size of coquelicot should be 128
  And contents of downloaded sample file should be same as sample local file

Scenario: Disable coquelicot application
  Given the coquelicot application is enabled
  When I disable the coquelicot application
  Then the coquelicot service should not be running
