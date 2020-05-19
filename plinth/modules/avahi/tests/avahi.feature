# SPDX-License-Identifier: AGPL-3.0-or-later

@system @essential @service_discovery
Feature: Service Discovery
  Configure service discovery.

Background:
  Given I'm a logged in user

Scenario: Disable service discovery application
  Given the service discovery application is enabled
  When I disable the service discovery application
  Then the service discovery service should not be running

Scenario: Enable service discovery application
  Given the service discovery application is disabled
  When I enable the service discovery application
  Then the service discovery service should be running
