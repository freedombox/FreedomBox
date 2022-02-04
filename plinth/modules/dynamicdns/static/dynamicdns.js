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
    var NOIP = 'https://<User>:<Pass>@dynupdate.no-ip.com/nic/update?' +
        'hostname=<Domain>';
    var FREEDNS = 'https://freedns.afraid.org/dynamic/update.php?' +
        '_YOURAPIKEYHERE_';

    $('#id_service_type').change(function() {
        set_mode();

        var service_type = $("#id_service_type").val();
        if (service_type == "noip.com") {
            $('#id_update_url').val(NOIP);
        } else if (service_type == "freedns.afraid.org") {
            $('#id_update_url').val(FREEDNS);
        } else {  // GnuDIP and other
            $('#id_update_url').val('');
        }
    });

    $('#id_show_password').change(function() {
        if ($('#id_show_password').prop('checked')) {
            $('#id_password').prop('type', 'text');
        } else {
            $('#id_password').prop('type', 'password');
        }
    });

    function set_mode() {
        var service_type = $("#id_service_type").val();
        if (service_type == "gnudip") {
            set_gnudip_mode();
        } else {
            set_update_url_mode();
        }
    }

    function set_gnudip_mode() {
        $('.form-group').show();
        $('#id_update_url').closest('.form-group').hide();
        $('#id_disable_ssl_cert_check').closest('.form-group').hide();
        $('#id_use_http_basic_auth').closest('.form-group').hide();
        $('#id_use_ipv6').closest('.form-group').hide();
        $('#id_server').closest('.form-group').show();
    }

    function set_update_url_mode() {
        $('#id_update_url').closest('.form-group').show();
        $('#id_disable_ssl_cert_check').closest('.form-group').show();
        $('#id_use_http_basic_auth').closest('.form-group').show();
        $('#id_use_ipv6').closest('.form-group').show();
        $('#id_server').closest('.form-group').hide();
    }

    set_mode();
})(jQuery);
