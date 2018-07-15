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

@apps @matrixsynapse
Feature: Matrix Synapse VoIP and Chat Server
  Run Matrix Synapse server

Background:
  Given I'm a logged in user
  Given the domain name is set to mydomain
  Given the matrixsynapse application is installed
  Given the domain name for matrixsynapse is set to mydomain

Scenario: Enable matrixsynapse application
  Given the matrixsynapse application is disabled
  When I enable the matrixsynapse application
  Then the matrixsynapse service should be running

Scenario: Disable matrixsynapse application
  Given the matrixsynapse application is enabled
  When I disable the matrixsynapse application
  Then the matrixsynapse service should not be running
