# SPDX-License-Identifier: AGPL-3.0-or-later

# TODO Scenario: Visit the wiki
# TODO Scenario: Visit the mailing list
# TODO Scenario: Visit the IRC channel
# TODO Scenario: View the manual
# TODO Scenario: View the about page

@help @system @essential
Feature: Help module
  Show various information about the system.

Background:
  Given I'm a logged in user

Scenario: Status logs
  When I go to the status logs page
  Then status logs should be shown
