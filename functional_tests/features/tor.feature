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

@apps @tor-app @backups
Feature: Tor Anonymity Network
  Manage Tor configuration.

Background:
  Given I'm a logged in user
  Given the tor application is installed

Scenario: Enable tor application
  Given the tor application is disabled
  When I enable the tor application
  Then the tor service should be running

Scenario: Set tor relay configuration
  Given tor relay is disabled
  When I enable tor relay
  Then tor relay should be enabled
  And tor orport port should be displayed

Scenario: Set tor bridge relay configuration
  Given tor bridge relay is disabled
  When I enable tor bridge relay
  Then tor bridge relay should be enabled
  And tor obfs3 port should be displayed
  And tor obfs4 port should be displayed

Scenario: Set tor hidden services configuration
  Given tor hidden services are disabled
  When I enable tor hidden services
  Then tor hidden services should be enabled
  And tor hidden services information should be displayed

Scenario: Set download software packages over tor
  Given download software packages over tor is disabled
  When I enable download software packages over tor
  Then download software packages over tor should be enabled

# TODO: Test more thoroughly by checking same hidden service is restored and by
# actually connecting using Tor.
Scenario: Backup and restore tor
  Given the tor application is enabled
  And tor relay is enabled
  And tor bridge relay is enabled
  And tor hidden services are enabled
  When I create a backup of the tor app data
  And I disable tor relay
  And I disable tor hidden services
  And I export the tor app data backup
  And I restore the tor app data backup
  Then the tor service should be running
  And tor relay should be enabled
  And tor bridge relay should be enabled
  And tor hidden services should be enabled

Scenario: Disable tor application
  Given the tor application is enabled
  When I disable the tor application
  Then the tor service should not be running
