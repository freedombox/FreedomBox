# SPDX-License-Identifier: AGPL-3.0-or-later

@system @performance
Feature: Performance - system monitoring
  Run the Performance Co-Pilot app.

Background:
  Given I'm a logged in user
  And advanced mode is on
  And the performance application is installed

Scenario: Enable performance application
  Given the performance application is disabled
  When I enable the performance application
  Then the performance service should be running

Scenario: Disable performance application
  Given the performance application is enabled
  When I disable the performance application
  Then the performance service should not be running
