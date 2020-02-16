// SPDX-License-Identifier: AGPL-3.0-or-later
/**
 * @licstart The following is the entire license notice for the JavaScript
 * code in this page.
 *
 * This file is part of FreedomBox.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * @licend The above is the entire license notice for the JavaScript code
 * in this page.
 */

(function($) {
    $('#id_tor-relay_enabled').change(function() {
        var bridge = $('#id_tor-bridge_relay_enabled');
        var disable = !$('#id_tor-relay_enabled').prop('checked');
        bridge.prop('disabled', disable);
        if (disable) {
            $('#id_tor-bridge_relay_enabled').prop('checked', false);
        }
    }).change();

    $('#id_tor-use_upstream_bridges').change(function() {
        if ($('#id_tor-use_upstream_bridges').prop('checked')) {
            $('#id_tor-upstream_bridges').parent().parent().show('slow');
            $('#id_tor-relay_enabled').prop('checked', false)
                .prop('disabled', true);
            $('#id_tor-bridge_relay_enabled').prop('checked', false)
                .prop('disabled', true);
        } else {
            $('#id_tor-upstream_bridges').parent().parent().hide('slow');
            $('#id_tor-relay_enabled').prop('disabled', false);
        }
    }).change();
})(jQuery);
