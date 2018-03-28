#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

@apps @sharing
Feature: Sharing
  Share server folders over HTTP, etc.

Background:
  Given I'm a logged in user

Scenario: Add new share
  Given share tmp is not available
  When I add a share tmp from path /tmp for admin
  Then the share tmp should be listed from path /tmp for admin
  And the share tmp should be accessible

Scenario: Edit a share
  Given share tmp is not available
  When I remove share boot
  And I add a share tmp from path /tmp for admin
  And I edit share tmp to boot from path /boot for admin
  Then the share tmp should not be listed
  And the share tmp should not exist
  And the share boot should be listed from path /boot for admin
  And the share boot should be accessible

Scenario: Remove a share
  When I remove share tmp
  And I add a share tmp from path /tmp for admin
  And I remove share tmp
  Then the share tmp should not be listed
  And the share tmp should not exist

Scenario: Share permissions
  When I remove share tmp
  And I add a share tmp from path /tmp for syncthing
  Then the share tmp should be listed from path /tmp for syncthing
  And the share tmp should not be accessible
