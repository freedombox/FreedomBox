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

@apps @bind @backups
Feature: Bind Domain Name Server
  Configure the Bind Domain Name Server.

Background:
  Given I'm a logged in user
  Given the bind application is installed

Scenario: Enable bind application
  Given the bind application is disabled
  When I enable the bind application
  Then the bind service should be running

Scenario: Disable bind application
  Given the bind application is enabled
  When I disable the bind application
  Then the bind service should not be running

Scenario: Set bind forwarders
  Given the bind application is enabled
  And bind forwarders are set to 1.1.1.1
  When I set bind forwarders to 1.1.1.1 1.0.0.1
  Then bind forwarders should be 1.1.1.1 1.0.0.1

Scenario: Enable bind DNSSEC
  Given the bind application is enabled
  And bind DNSSEC is disabled
  When I enable bind DNSSEC
  Then bind DNSSEC should be enabled

Scenario: Disable bind DNSSEC
  Given the bind application is enabled
  And bind DNSSEC is disabled
  When I disable bind DNSSEC
  Then bind DNSSEC should be disabled

Scenario: Backup and restore bind
  Given the bind application is enabled
  When I set bind forwarders to 1.1.1.1
  And I disable bind DNSSEC
  And I create a backup of the bind app data
  And I set bind forwarders to 1.0.0.1
  And I enable bind DNSSEC
  And I restore the bind app data backup
  Then bind forwarders should be 1.1.1.1
  And bind DNSSEC should be disabled

Scenario: Download, upload and restore a backup
  Given the bind application is enabled
  When I set bind forwarders to 1.1.1.1
  And I create a backup of the bind app data
  And I set bind forwarders to 1.0.0.1
  And I download the bind app data backup
  And I restore the downloaded bind app data backup
  Then bind forwarders should be 1.1.1.1
