# SPDX-License-Identifier: AGPL-3.0-or-later

# TODO Scenario: Configure GnuDIP service
# TODO Scenario: Configure noip.com service
# TODO Scenario: Configure selfhost.bz service
# TODO Scenario: Configure freedns.afraid.org service
# TODO Scenario: Configure other update URL service

@apps @dynamicdns
Feature: Dynamic DNS Client
  Update public IP to a GnuDIP server.

Background:
  Given I'm a logged in user
  And the dynamicdns application is installed

Scenario: Capitalized domain name
  Given dynamicdns is configured
  When I change the domain name to FreedomBox.example.com
  Then the domain name should be freedombox.example.com

@backups
Scenario: Backup and restore configuration
  Given dynamicdns is configured
  When I create a backup of the dynamicdns app data with name test_dynamicdns
  And I change the dynamicdns configuration
  And I restore the dynamicdns app data backup with name test_dynamicdns
  Then dynamicdns should have the original configuration
