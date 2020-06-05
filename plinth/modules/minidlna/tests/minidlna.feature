# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @minidlna
Feature: minidlna Simple Media Server
  Run miniDLNA media server

Background:
  Given I'm a logged in user
  And the minidlna application is installed

Scenario: Enable minidlna application
  Given the minidlna application is disabled
  When I enable the minidlna application
  Then the minidlna service should be running

Scenario: Disable minidlna application
  Given the minidlna application is enabled
  When I disable the minidlna application
  Then the minidlna service should not be running
