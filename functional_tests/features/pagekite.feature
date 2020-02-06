# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @pagekite @backups
Feature: Pagekite Public Visibility
  Configure Pagekite public visitbility server.

Background:
  Given I'm a logged in user
  Given the pagekite application is installed

Scenario: Enable pagekite application
  Given the pagekite application is disabled
  When I enable the pagekite application
  Then the pagekite service should be running

Scenario: Configure pagekite application
  Given the pagekite application is enabled
  When I configure pagekite with host pagekite.example.com, port 8080, kite name mykite.example.com and kite secret mysecret
  Then pagekite should be configured with host pagekite.example.com, port 8080, kite name mykite.example.com and kite secret mysecret

Scenario: Backup and restore pagekite
  Given the pagekite application is enabled
  When I configure pagekite with host beforebackup.example.com, port 8081, kite name beforebackup.example.com and kite secret beforebackupsecret
  And I create a backup of the pagekite app data with name test_pagekite
  And I configure pagekite with host afterbackup.example.com, port 8082, kite name afterbackup.example.com and kite secret afterbackupsecret
  And I restore the pagekite app data backup with name test_pagekite
  Then the pagekite service should be running
  And pagekite should be configured with host beforebackup.example.com, port 8081, kite name beforebackup.example.com and kite secret beforebackupsecret

Scenario: Disable pagekite application
  Given the pagekite application is enabled
  When I disable the pagekite application
  Then the pagekite service should not be running
