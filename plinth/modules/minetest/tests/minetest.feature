# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @minetest
Feature: Minetest Block Sandbox
  Run the Minetest server

Background:
  Given I'm a logged in user
  Given the minetest application is installed

Scenario: Enable minetest application
  Given the minetest application is disabled
  When I enable the minetest application
  Then the minetest service should be running

Scenario: Disable minetest application
  Given the minetest application is enabled
  When I disable the minetest application
  Then the minetest service should not be running
