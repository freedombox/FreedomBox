# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @i2p
Feature: I2P Anonymity Network
  Manage I2P configuration.

Background:
  Given I'm a logged in user
  Given the i2p application is installed

Scenario: Enable i2p application
  Given the i2p application is disabled
  When I enable the i2p application
  Then the i2p service should be running

Scenario: Disable i2p application
  Given the i2p application is enabled
  When I disable the i2p application
  Then the i2p service should not be running
