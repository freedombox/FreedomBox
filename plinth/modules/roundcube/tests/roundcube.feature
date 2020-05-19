# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @roundcube
Feature: Roundcube Email Client
  Run webmail client.

Background:
  Given I'm a logged in user
  Given the roundcube application is installed

Scenario: Enable roundcube application
  Given the roundcube application is disabled
  When I enable the roundcube application
  Then the roundcube site should be available

@backups
Scenario: Backup and restore roundcube
  Given the roundcube application is enabled
  When I create a backup of the roundcube app data with name test_roundcube
  And I restore the roundcube app data backup with name test_roundcube
  Then the roundcube site should be available

Scenario: Disable roundcube application
  Given the roundcube application is enabled
  When I disable the roundcube application
  Then the roundcube site should not be available
