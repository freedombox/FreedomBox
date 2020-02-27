# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @transmission @backups @sso
Feature: Transmission BitTorrent Client
  Run the Transmission BitTorrent client.

Background:
  Given I'm a logged in user
  Given the transmission application is installed

Scenario: Enable transmission application
  Given the transmission application is disabled
  When I enable the transmission application
  Then the transmission site should be available

Scenario: Upload a torrent to transmission
  Given the transmission application is enabled
  When all torrents are removed from transmission
  And I upload a sample torrent to transmission
  Then there should be 1 torrents listed in transmission

Scenario: Backup and restore transmission
  Given the transmission application is enabled
  When all torrents are removed from transmission
  And I upload a sample torrent to transmission
  And I create a backup of the transmission app data
  And all torrents are removed from transmission
  And I restore the transmission app data backup
  Then the transmission service should be running
  And there should be 1 torrents listed in transmission

Scenario: Disable transmission application
  Given the transmission application is enabled
  When I disable the transmission application
  Then the transmission site should not be available
