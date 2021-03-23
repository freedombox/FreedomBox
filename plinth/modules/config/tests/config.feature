# SPDX-License-Identifier: AGPL-3.0-or-later

@system @essential @config
Feature: Configuration
  Configure the system.

Background:
  Given I'm a logged in user

Scenario: Change hostname
  When I change the hostname to mybox
  Then the hostname should be mybox

Scenario: Change domain name
  When I change the domain name to mydomain.example
  Then the domain name should be mydomain.example

Scenario: Capitalized domain name
  When I change the domain name to Mydomain.example
  Then the domain name should be mydomain.example

Scenario: Change webserver home page
  Given the syncthing application is installed
  And the syncthing application is enabled
  And the home page is syncthing
  When I change the home page to plinth
  Then the home page should be plinth
