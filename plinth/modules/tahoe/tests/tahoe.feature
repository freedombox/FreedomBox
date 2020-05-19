# SPDX-License-Identifier: AGPL-3.0-or-later

# TODO: When tahoe-lafs is restarted, it leaves a .gnupg folder in
# /var/lib/tahoe-lafs and failes to start in the next run. Enable tests after
# this is fixed.

@apps @tahoe @skip
Feature: Tahoe-LAFS distribute file storage
  Run the Tahoe distribute file storage server

Background:
  Given I'm a logged in user
  And advanced mode is on
  And the domain name is set to mydomain.example
  And the tahoe application is installed
  And the domain name for tahoe is set to mydomain.example

Scenario: Enable tahoe application
  Given the tahoe application is disabled
  When I enable the tahoe application
  Then the tahoe service should be running

Scenario: Default tahoe introducers
  Given the tahoe application is enabled
  Then mydomain.example should be a tahoe local introducer
  And mydomain.example should be a tahoe connected introducer

Scenario: Add tahoe introducer
  Given the tahoe application is enabled
  And anotherdomain.example is not a tahoe introducer
  When I add anotherdomain.example as a tahoe introducer
  Then anotherdomain.example should be a tahoe connected introducer

Scenario: Remove tahoe introducer
  Given the tahoe application is enabled
  And anotherdomain.example is a tahoe introducer
  When I remove anotherdomain.example as a tahoe introducer
  Then anotherdomain.example should not be a tahoe connected introducer

@backups
Scenario: Backup and restore tahoe
  Given the tahoe application is enabled
  And backupdomain.example is a tahoe introducer
  When I create a backup of the tahoe app data with name test_tahoe
  And I remove backupdomain.example as a tahoe introducer
  And I restore the tahoe app data backup with name test_tahoe
  Then the tahoe service should be running
  And backupdomain.example should be a tahoe connected introducer

Scenario: Disable tahoe application
  Given the tahoe application is enabled
  When I disable the tahoe application
  Then the tahoe service should not be running
