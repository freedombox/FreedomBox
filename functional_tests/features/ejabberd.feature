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

@apps @ejabberd
Feature: Ejabberd Chat Server
  Run ejabberd chat server.

Background:
  Given I'm a logged in user
  Given the ejabberd application is installed

Scenario: Enable ejabberd application
  Given the ejabberd application is disabled
  When I enable the ejabberd application
  Then the ejabberd service should be running

Scenario: Disable ejabberd application
  Given the ejabberd application is enabled
  When I disable the ejabberd application
  Then the ejabberd service should not be running

Scenario: Enable message archive management
  Given the ejabberd application is enabled
  When I enable message archive management
  Then the ejabberd service should be running

Scenario: Disable message archive management
  Given the ejabberd application is enabled
  When I disable message archive management
  Then the ejabberd service should be running
