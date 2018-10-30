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

# TODO: When tahoe-lafs is restarted, it leaves a .gnupg folder in
# /var/lib/tahoe-lafs and failes to start in the next run. Enable tests after
# this is fixed.

@apps @tahoe @skip
Feature: Tahoe-LAFS distribute file storage
  Run the Tahoe distribute file storage server

Background:
  Given I'm a logged in user
  And the domain name is set to mydomain.example
  And the tahoe application is installed
  And the domain name for tahoe is set to mydomain.example

Scenario: Enable tahoe application
  Given the tahoe application is disabled
  When I enable the tahoe application
  Then the tahoe service should be running

Scenario: Disable tahoe application
  Given the tahoe application is enabled
  When I disable the tahoe application
  Then the tahoe service should not be running

Scenario: Default tahoe introducers
  Given the tahoe application is enabled
  Then mydomain.example should be a tahoe local introducer
  And mydomain.example should be a tahoe connected introducer

Scenario: Add tahoe introducer
  Given the tahoe application is enabled
  And anotherdomain.example is not a tahoe introducer
  When I add anotherdomain.example as a tahoe introducer
  Then anotherdomain.example should be a tahoe connected introducer

Scenario: Remove tahoe introducer
  Given the tahoe application is enabled
  And anotherdomain.example is a tahoe introducer
  When I remove anotherdomain.example as a tahoe introducer
  Then anotherdomain.example should not be a tahoe connected introducer
