# SPDX-License-Identifier: AGPL-3.0-or-later

@apps @gitweb @backups @sso
Feature: gitweb Simple Git Hosting
  Git web interface.

Background:
  Given I'm a logged in user
  And the gitweb application is installed

Scenario: Enable gitweb application
  Given the gitweb application is disabled
  When I enable the gitweb application
  Then the gitweb site should be available

Scenario: Create public repository
  Given the gitweb application is enabled
  And a public repository that doesn't exist
  When I create the repository
  Then the repository should be listed as a public
  And the repository should be listed on gitweb

Scenario: Create private repository
  Given the gitweb application is enabled
  And a private repository that doesn't exist
  When I create the repository
  Then the repository should be listed as a private
  And the repository should be listed on gitweb

Scenario: Delete repository
  Given the gitweb application is enabled
  And a repository
  When I delete the repository
  Then the repository should not be listed

Scenario: Backup and restore gitweb
  Given the gitweb application is enabled
  And a repository
  When I create a backup of the gitweb app data
  And I delete the repository
  And I restore the gitweb app data backup
  Then the repository should be restored
  And the gitweb site should be available

Scenario: Disable gitweb application
  Given the gitweb application is enabled
  When I disable the gitweb application
  Then the gitweb site should not be available

Scenario: Public gitweb site shows only public repositories
  Given the gitweb application is enabled
  And both public and private repositories exist
  When I log out
  Then the public repository should be listed on gitweb
  And the private repository should not be listed on gitweb

Scenario: Gitweb is not public if there are only private repositories
  Given the gitweb application is enabled
  And at least one repository exists
  And all repositories are private
  When I log out
  And I access gitweb application
  Then I should be prompted for login
  And gitweb app should not be visible on the front page

Scenario: Edit repository metadata
  Given the gitweb application is enabled
  And a public repository that doesn't exist
  And a repository metadata:
     description: Test Description
     owner: Test Owner
     access: private
  When I create the repository
  And I set the metadata of the repository
  Then the metadata of the repository should be as set

Scenario: Access public repository with git client
  Given the gitweb application is enabled
  And a public repository
  When using a git client
  Then the repository should be publicly readable
  And the repository should not be publicly writable
  And the repository should be privately writable

Scenario: Access private repository with git client
  Given the gitweb application is enabled
  And a private repository
  When using a git client
  Then the repository should not be publicly readable
  And the repository should not be publicly writable
  And the repository should be privately readable
  And the repository should be privately writable
