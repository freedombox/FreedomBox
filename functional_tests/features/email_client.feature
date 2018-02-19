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

@apps @roundcube
Feature: Email Client
  Run webmail client.

Background:
  Given I'm a logged in user
  Given the roundcube application is installed

Scenario: Enable roundcube application
  Given the roundcube application is disabled
  When I enable the roundcube application
  Then the roundcube site should be available

Scenario: Disable roundcube application
  Given the roundcube application is enabled
  When I disable the roundcube application
  Then the roundcube site should not be available
