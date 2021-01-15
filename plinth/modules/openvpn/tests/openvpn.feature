# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @openvpn
Feature: OpenVPN - Virtual Private Network
  Setup and configure OpenVPN

Background:
  Given I'm a logged in user
  Given the openvpn application is installed

Scenario: Enable openvpn application
  Given the openvpn application is disabled
  When I enable the openvpn application
  Then the openvpn service should be running

Scenario: Download openvpn profile
  Given the openvpn application is enabled
  Then the openvpn profile should be downloadable

Scenario: User of 'vpn' group
  Given the openvpn application is enabled
  And the user vpnuser in group vpn exists
  When I'm logged in as the user vpnuser
  Then the openvpn profile should be downloadable

Scenario: User not of 'vpn' group
  Given the openvpn application is enabled
  And the user nonvpnuser exists
  When I'm logged in as the user nonvpnuser
  Then openvpn app should not be visible on the front page

@backups
Scenario: Backup and restore openvpn
  Given the openvpn application is enabled
  And I download openvpn profile
  When I create a backup of the openvpn app data with name test_openvpn
  And I restore the openvpn app data backup with name test_openvpn
  Then the openvpn profile downloaded should be same as before

Scenario: Disable openvpn application
  Given the openvpn application is enabled
  When I disable the openvpn application
  Then the openvpn service should not be running
