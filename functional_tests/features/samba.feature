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

@apps @samba @backups
Feature: Samba File Sharing
  Configure samba file sharing service.

Background:
  Given I'm a logged in user
  Given the network device is in the internal firewall zone
  Given the samba application is installed

Scenario: Enable samba application
  Given the samba application is disabled
  When I enable the samba application
  Then the samba service should be running

Scenario: Disable samba application
  Given the samba application is enabled
  When I disable the samba application
  Then the samba service should not be running

Scenario: Enable open samba share
  Given the samba application is enabled
  When I enable the open samba share
  Then I can write to the open samba share
  And a guest user can write to the open samba share

Scenario: Enable group samba share
  Given the samba application is enabled
  When I enable the group samba share
  Then I can write to the group samba share
  And a guest user can't access the group samba share

Scenario: Enable home samba share
  Given the samba application is enabled
  When I enable the home samba share
  Then I can write to the home samba share
  And a guest user can't access the home samba share

Scenario: Disable open samba share
  Given the samba application is enabled
  When I disable the open samba share
  Then the open samba share should not be available

Scenario: Backup and restore samba
  Given the samba application is enabled
  When I enable the home samba share
  And I create a backup of the samba app data
  And I disable the home samba share
  And I restore the samba app data backup
  Then the samba service should be running
  And I can write to the home samba share
