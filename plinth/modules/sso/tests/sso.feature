# SPDX-License-Identifier: AGPL-3.0-or-later

@sso @essential @system
Feature: Single Sign On
  Test Single Sign On features.

Background:
  Given I'm a logged in user
  Given the syncthing application is installed
  Given the syncthing application is enabled


Scenario: Logged out Plinth user cannot access Syncthing web interface
  Given I'm a logged out user
  When I access syncthing application
  Then I should be prompted for login

Scenario: Logged in Plinth user can access Syncthing web interface
  When I access syncthing application
  Then the syncthing site should be available
