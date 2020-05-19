# SPDX-License-Identifier: AGPL-3.0-or-later

@system @storage @essential
Feature: Storage
  Show information about the disks.

Background:
  Given I'm a logged in user

Scenario: List disks
  Given I'm on the storage page
  Then the root disk should be shown
