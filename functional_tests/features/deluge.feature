# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @deluge @backups
Feature: Deluge BitTorrent Client
  Run the Deluge BitTorrent client.

Background:
  Given I'm a logged in user
  Given the deluge application is installed

Scenario: Enable deluge application
  Given the deluge application is disabled
  When I enable the deluge application
  Then the deluge site should be available

Scenario: Upload a torrent to deluge
  Given the deluge application is enabled
  When all torrents are removed from deluge
  And I upload a sample torrent to deluge
  Then there should be 1 torrents listed in deluge

Scenario: Backup and restore deluge
  Given the deluge application is enabled
  When all torrents are removed from deluge
  And I upload a sample torrent to deluge
  And I create a backup of the deluge app data with name test_deluge
  And all torrents are removed from deluge
  And I restore the deluge app data backup with name test_deluge
  Then the deluge service should be running
  And there should be 1 torrents listed in deluge

Scenario: Disable deluge application
  Given the deluge application is enabled
  When I disable the deluge application
  Then the deluge site should not be available
