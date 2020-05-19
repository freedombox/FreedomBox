# SPDX-License-Identifier: AGPL-3.0-or-later

# TODO Scenario: Add user to wiki group
# TODO Scenario: Remove user from wiki group
# TODO Scenario: Set user SSH key
# TODO Scenario: Clear user SSH key
# TODO Scenario: Make user inactive
# TODO Scenario: Make user active
# TODO Scenario: Change user password

@system @essential @users_groups
Feature: Users and Groups
  Manage users and groups.

Background:
  Given I'm a logged in user

Scenario: Create user
  Given the user alice doesn't exist
  When I create a user named alice with password secret123secret123
  Then alice should be listed as a user

Scenario: Rename user
  Given the user alice exists
  Given the user bob doesn't exist
  When I rename the user alice to bob
  Then alice should not be listed as a user
  Then bob should be listed as a user

Scenario: Delete user
  Given the user alice exists
  When I delete the user alice
  Then alice should not be listed as a user

Scenario Outline: Change language
  When I change the language to <language>
  Then Plinth language should be <language>

  Examples:
  | language       |
  | dansk          |
  | Deutsch        |
  | español        |
  | français       |
  | norsk (bokmål) |
  | Nederlands     |
  | polski         |
  | Português      |
  | Русский        |
  | svenska        |
  | తెలుగు          |
  | Türkçe         |
  | 简体中文       |
