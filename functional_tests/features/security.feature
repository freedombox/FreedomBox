# SPDX-License-Identifier: AGPL-3.0-or-later

@security @essential @system
Feature: Security
  Configure security options.

Background:
  Given I'm a logged in user

Scenario: Disable restricted console logins
  Given restricted console logins are enabled
  When I disable restricted console logins
  Then restricted console logins should be disabled

Scenario: Backup and restore security
  When I enable restricted console logins
  And I create a backup of the security app data
  And I disable restricted console logins
  And I restore the security app data backup
  Then restricted console logins should be enabled

Scenario: Enable restricted console logins
  Given restricted console logins are disabled
  When I enable restricted console logins
  Then restricted console logins should be enabled
