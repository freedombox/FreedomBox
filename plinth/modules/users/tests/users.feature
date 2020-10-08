# SPDX-License-Identifier: AGPL-3.0-or-later

# TODO Scenario: Add user to wiki group
# TODO Scenario: Remove user from wiki group

@system @essential @users
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

Scenario: Admin users can change their own ssh keys
  When I change the ssh keys to somekey123
  Then the ssh keys should be somekey123

Scenario: Non-admin users can change their own ssh keys
  Given the user alice with password secret123secret123 exists
  And I'm logged in as the user alice with password secret123secret123
  When I change my ssh keys to somekey456 with password secret123secret123
  Then my ssh keys should be somekey456

Scenario: Admin users can change other user's ssh keys
  Given the user alice exists
  When I change the ssh keys to alicesomekey123 for the user alice
  Then the ssh keys should be alicesomekey123 for the user alice

Scenario: Users can remove ssh keys
  Given the ssh keys are somekey123
  When I remove the ssh keys
  Then the ssh keys should be removed

Scenario: Users can connect passwordless over ssh if the keys are set
  Given the ssh application is enabled
  And the client has a ssh key
  When I configure the ssh keys
  Then the client should be able to connect passwordless over ssh

Scenario: Users can't connect passwordless over ssh if the keys aren't set
  Given the ssh application is enabled
  And the client has a ssh key
  And the ssh keys are configured
  When I remove the ssh keys
  Then the client shouldn't be able to connect passwordless over ssh


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
  | None           |

Scenario: Admin users can set other users an inactive
  Given the user alice with password secret789secret789 exists
  When I set the user alice as inactive
  Then I can't log in as the user alice with password secret789secret789

Scenario: Admin users can change their own password
  Given the admin user testadmin with password testingtesting123 exists
  And I'm logged in as the user testadmin with password testingtesting123
  When I change my password from testingtesting123 to testingtesting456
  Then I can log in as the user testadmin with password testingtesting456

Scenario: Admin user can change other user's password
  Given the user alice exists
  When I change the user alice password to secretsecret567
  Then I can log in as the user alice with password secretsecret567

Scenario: Non-admin users can change their own password
  Given the user alice with password secret123secret123 exists
  And I'm logged in as the user alice with password secret123secret123
  When I change my password from secret123secret123 to secret456secret456
  Then I can log in as the user alice with password secret456secret456

Scenario: Delete user
  Given the user alice exists
  When I delete the user alice
  Then alice should not be listed as a user
