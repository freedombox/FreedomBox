# SPDX-License-Identifier: AGPL-3.0-or-later

@system @essential @avahi
Feature: Avahi Service Discovery
  Configure service discovery.

Background:
  Given I'm a logged in user

Scenario: Disable avahi application
  Given the avahi application is enabled
  When I disable the avahi application
  Then the avahi service should not be running

Scenario: Enable avahi application
  Given the avahi application is disabled
  When I enable the avahi application
  Then the avahi service should be running
