# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @mediawiki @backups
Feature: MediaWiki Wiki Engine
  Manage wikis, multimedia and more.

Background:
  Given I'm a logged in user
  Given the mediawiki application is installed

Scenario: Enable mediawiki application
  Given the mediawiki application is disabled
  When I enable the mediawiki application
  Then the mediawiki site should be available

Scenario: Enable public registrations
  Given the mediawiki application is enabled
  When I enable mediawiki public registrations
  Then the mediawiki site should allow creating accounts

Scenario: Disable public registrations
  Given the mediawiki application is enabled
  When I disable mediawiki public registrations
  Then the mediawiki site should not allow creating accounts

Scenario: Enable private mode
  Given the mediawiki application is enabled
  When I enable mediawiki private mode
  Then the mediawiki site should not allow creating accounts
  Then the mediawiki site should not allow anonymous reads and writes

Scenario: Disable private mode
  Given the mediawiki application is enabled
  When I disable mediawiki private mode
  Then the mediawiki site should allow anonymous reads and writes

Scenario: Enabling private mode disables public registrations
  Given the mediawiki application is enabled
  When I enable mediawiki public registrations
  And I enable mediawiki private mode
  Then the mediawiki site should not allow creating accounts

# Requires JS
Scenario: Enabling public registrations disables private mode
  Given the mediawiki application is enabled
  When I enable mediawiki private mode
  And I enable mediawiki public registrations
  Then the mediawiki site should allow creating accounts

# Requires JS
Scenario: Logged in user can see upload files option
  Given the mediawiki application is enabled
  When I set the mediawiki admin password to whatever123
  Then I should see the Upload File option in the side pane when logged in with credentials admin and whatever123

Scenario: Upload images
  Given the mediawiki application is enabled
  When I upload an image named noise.png to mediawiki with credentials admin and whatever123
  Then there should be Noise.png image

Scenario: Upload SVG image
  Given the mediawiki application is enabled
  When I upload an image named apps-background.svg to mediawiki with credentials admin and whatever123
  Then there should be Apps-background.svg image

Scenario: Backup and restore mediawiki
  Given the mediawiki application is enabled
  When I create a backup of the mediawiki app data with name test_mediawiki
  When I enable mediawiki public registrations
  And I delete the mediawiki main page
  And I restore the mediawiki app data backup with name test_mediawiki
  Then the mediawiki main page should be restored
  Then the mediawiki site should allow creating accounts

Scenario: Disable mediawiki application
  Given the mediawiki application is enabled
  When I disable the mediawiki application
  Then the mediawiki site should not be available
