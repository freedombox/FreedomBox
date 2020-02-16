# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @sharing @backups
Feature: Sharing
  Share server folders over HTTP, etc.

Background:
  Given I'm a logged in user

Scenario: Add new share
  Given share tmp is not available
  When I add a share tmp from path /tmp for admin
  Then the share tmp should be listed from path /tmp for admin
  And the share tmp should be accessible

Scenario: Edit a share
  Given share tmp is not available
  When I remove share boot
  And I add a share tmp from path /tmp for admin
  And I edit share tmp to boot from path /boot for admin
  Then the share tmp should not be listed
  And the share tmp should not exist
  And the share boot should be listed from path /boot for admin
  And the share boot should be accessible

Scenario: Remove a share
  When I remove share tmp
  And I add a share tmp from path /tmp for admin
  And I remove share tmp
  Then the share tmp should not be listed
  And the share tmp should not exist

Scenario: Share permissions
  When I remove share tmp
  And I add a share tmp from path /tmp for syncthing
  Then the share tmp should be listed from path /tmp for syncthing
  And the share tmp should not be accessible

Scenario: Public share
  When I edit share tmp to be public
  And I log out
  Then the share_tmp site should be available

Scenario: Backup and restore sharing
  Given share tmp is not available
  When I add a share tmp from path /tmp for admin
  And I create a backup of the sharing app data
  And I remove share tmp
  And I restore the sharing app data backup
  Then the share tmp should be listed from path /tmp for admin
  And the share tmp should be accessible
