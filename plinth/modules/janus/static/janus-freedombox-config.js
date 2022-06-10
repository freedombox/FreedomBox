// SPDX-License-Identifier: AGPL-3.0-or-later
/*
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
*/

var server = "/janus";
var iceServers = null;
var token = "";
var apisecret = "";

$(document).ready(function() {
    const body = document.querySelector('body');
    const config = JSON.parse(body.getAttribute('data-user-turn-config'));
    iceServers = [{urls: config['uris'],
                   username: config['username'],
                   credential: config['credential']}];
});
