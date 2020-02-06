# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @shadowsocks @backups
Feature: Shadowsocks Socks5 Proxy
  Run the Shadowsocks Socks5 proxy client.

Background:
  Given I'm a logged in user
  Given the shadowsocks application is installed
  Given the shadowsocks application is configured

Scenario: Enable shadowsocks application
  Given the shadowsocks application is disabled
  When I enable the shadowsocks application
  Then the shadowsocks service should be running

Scenario: Backup and restore shadowsocks
  Given the shadowsocks application is enabled
  When I configure shadowsocks with server example.com and password beforebackup123
  And I create a backup of the shadowsocks app data with name test_shadowsocks
  And I configure shadowsocks with server example.org and password afterbackup123
  And I restore the shadowsocks app data backup with name test_shadowsocks
  Then the shadowsocks service should be running
  And shadowsocks should be configured with server example.com and password beforebackup123

Scenario: Disable shadowsocks application
  Given the shadowsocks application is enabled
  When I disable the shadowsocks application
  Then the shadowsocks service should not be running
