# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @radicale
Feature: Radicale Calendar and Addressbook
  Configure CalDAV/CardDAV server.

Background:
  Given I'm a logged in user
  Given the radicale application is installed

Scenario: Enable radicale application
  Given the radicale application is disabled
  When I enable the radicale application
  Then the radicale service should be running
  And the calendar should be available
  And the addressbook should be available

Scenario: Owner-only access rights
  Given the radicale application is enabled
  And the access rights are set to "any user can view, but only the owner can make changes"
  When I change the access rights to "only the owner can view or make changes"
  Then the radicale service should be running
  And the access rights should be "only the owner can view or make changes"

Scenario: Owner-write access rights
  Given the radicale application is enabled
  And the access rights are set to "only the owner can view or make changes"
  When I change the access rights to "any user can view, but only the owner can make changes"
  Then the radicale service should be running
  And the access rights should be "any user can view, but only the owner can make changes"

Scenario: Authenticated access rights
  Given the radicale application is enabled
  And the access rights are set to "only the owner can view or make changes"
  When I change the access rights to "any user can view or make changes"
  Then the radicale service should be running
  And the access rights should be "any user can view or make changes"

Scenario: Disable radicale application
  Given the radicale application is enabled
  When I disable the radicale application
  Then the radicale service should not be running
  And the calendar should not be available
  And the addressbook should not be available
