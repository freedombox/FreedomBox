# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @infinoted
Feature: Infinoted Collaborative Text Editor
  Run Gobby Server - Infinoted

Background:
  Given I'm a logged in user
  Given the infinoted application is installed

Scenario: Enable infinoted application
  Given the infinoted application is disabled
  When I enable the infinoted application
  Then the infinoted service should be running

Scenario: Disable infinoted application
  Given the infinoted application is enabled
  When I disable the infinoted application
  Then the infinoted service should not be running
