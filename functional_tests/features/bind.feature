# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @bind @backups
Feature: Bind Domain Name Server
  Configure the Bind Domain Name Server.

Background:
  Given I'm a logged in user
  Given the bind application is installed

Scenario: Enable bind application
  Given the bind application is disabled
  When I enable the bind application
  Then the bind service should be running

Scenario: Set bind forwarders
  Given the bind application is enabled
  And bind forwarders are set to 1.1.1.1
  When I set bind forwarders to 1.1.1.1 1.0.0.1
  Then bind forwarders should be 1.1.1.1 1.0.0.1

Scenario: Enable bind DNSSEC
  Given the bind application is enabled
  And bind DNSSEC is disabled
  When I enable bind DNSSEC
  Then bind DNSSEC should be enabled

Scenario: Disable bind DNSSEC
  Given the bind application is enabled
  And bind DNSSEC is disabled
  When I disable bind DNSSEC
  Then bind DNSSEC should be disabled

Scenario: Backup and restore bind
  Given the bind application is enabled
  When I set bind forwarders to 1.1.1.1
  And I disable bind DNSSEC
  And I create a backup of the bind app data with name test_bind
  And I set bind forwarders to 1.0.0.1
  And I enable bind DNSSEC
  And I restore the bind app data backup with name test_bind
  Then bind forwarders should be 1.1.1.1
  And bind DNSSEC should be disabled

Scenario: Disable bind application
  Given the bind application is enabled
  When I disable the bind application
  Then the bind service should not be running
