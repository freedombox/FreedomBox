# SPDX-License-Identifier: AGPL-3.0-or-later

@help @system @essential
Feature: Help module
  Show various information about the system.

Background:
  Given I'm a logged in user

Scenario: Status logs
  When I go to the status logs page
  Then status logs should be shown
