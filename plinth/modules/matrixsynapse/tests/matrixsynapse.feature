# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @matrixsynapse
Feature: Matrix Synapse VoIP and Chat Server
  Run Matrix Synapse server

Background:
  Given I'm a logged in user
  Given the domain name is set to mydomain.example
  Given the matrixsynapse application is installed
  Given the domain name for matrixsynapse is set to mydomain.example

Scenario: Enable matrixsynapse application
  Given the matrixsynapse application is disabled
  When I enable the matrixsynapse application
  Then the matrixsynapse service should be running

Scenario: Disable matrixsynapse application
  Given the matrixsynapse application is enabled
  When I disable the matrixsynapse application
  Then the matrixsynapse service should not be running
