# SPDX-License-Identifier: AGPL-3.0-or-later

@system
Feature: Server Administration
  Run server administration application - Cockpit.

Background:
  Given I'm a logged in user
  Given the cockpit application is installed

Scenario: Enable cockpit application
  Given the cockpit application is disabled
  When I enable the cockpit application
  Then the cockpit site should be available

Scenario: Disable cockpit application
  Given the cockpit application is enabled
  When I disable the cockpit application
  Then the cockpit site should not be available
