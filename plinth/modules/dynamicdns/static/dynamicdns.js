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
    var SELFHOST = 'https://carol.selfhost.de/update?username=<User>&' +
        'password=<Pass>&myip=<Ip>';
    var NOIP = 'http://dynupdate.no-ip.com/nic/update?hostname=' +
        '<Domain>&myip=<Ip>';
    var FREEDNS = 'https://freedns.afraid.org/dynamic/update.php?' +
        '_YOURAPIKEYHERE_';

    // Hide all form fields
    $('.form-group').hide();
    // Show the enable checkbox
    $('#id_enabled').closest('.form-group').show();
    if ($('#id_enabled').prop('checked')) {
        // Show all form fields
        show_all();
        // Set the selectbox to the last configured value
        select_service();
    }

    $('#id_enabled').change(function() {
        if ($('#id_enabled').prop('checked')) {
            show_all();
            if ($("#id_service_type option:selected").text() == "GnuDIP") {
                set_gnudip_mode();
            } else {
                set_update_url_mode();
            }
        } else {
            $('.form-group').hide();
            $('#id_enabled').closest('.form-group').show();
        }
    });

    $('#id_service_type').change(function() {
        var service_type = $("#id_service_type option:selected").text();
        if (service_type == "GnuDIP") {
            set_gnudip_mode();
        } else {
            set_update_url_mode();
            if (service_type == "noip.com") {
                $('#id_dynamicdns_update_url').val(NOIP);
                $('#id_use_http_basic_auth').prop('checked', true);
            } else {
                $('#id_use_http_basic_auth').prop('checked', false);
            }
            if (service_type == "selfhost.bz") {
                $('#id_dynamicdns_update_url').val(SELFHOST);
            }
            if (service_type == "freedns.afraid.org") {
                $('#id_dynamicdns_update_url').val(FREEDNS);
            }
            if (service_type == "other update URL") {
                $('#id_dynamicdns_update_url').val('');
            }
        }
    });

    $('#id_showpw').change(function() {
        // Changing type attribute from password to text is prevented by most
        // browsers make a new form field works for me
        if ($('#id_showpw').prop('checked')) {
            $('#id_dynamicdns_secret').replaceWith(
                $('#id_dynamicdns_secret').clone().attr(
                    'type', 'text'));
        } else {
            $('#id_dynamicdns_secret').replaceWith(
                $('#id_dynamicdns_secret').clone().attr(
                    'type', 'password'));
        }
    });

    function select_service() {
        var update_url = $("#id_dynamicdns_update_url").val();
        if ($("#id_dynamicdns_server").val().length == 0) {
            set_update_url_mode();
            if (update_url == NOIP) {
                $("#id_service_type").val("noip");
            } else if (update_url == SELFHOST) {
                $("#id_service_type").val("selfhost");
            } else if (update_url == FREEDNS) {
                $("#id_service_type").val("freedns");
            } else {
                $("#id_service_type").val("other");
            }
        } else {
            $("#id_service_type").val("GnuDIP");
            set_gnudip_mode();
        }
    }

    function set_gnudip_mode() {
        $('#id_dynamicdns_update_url').closest('.form-group').hide();
        $('#id_disable_SSL_cert_check').closest('.form-group').hide();
        $('#id_use_http_basic_auth').closest('.form-group').hide();
        $('#id_dynamicdns_server').closest('.form-group').show();
    }

    function set_update_url_mode() {
        $('#id_dynamicdns_update_url').closest('.form-group').show();
        $('#id_disable_SSL_cert_check').closest('.form-group').show();
        $('#id_use_http_basic_auth').closest('.form-group').show();
        $('#id_dynamicdns_server').closest('.form-group').hide();
    }

    function show_all() {
        $('#id_enabled').closest('.form-group').show();
        $('#id_service_type').closest('.form-group').show();
        $('#id_dynamicdns_server').closest('.form-group').show();
        $('#id_dynamicdns_update_url').closest('.form-group').show();
        $('#id_disable_SSL_cert_check').closest('.form-group').show();
        $('#id_use_http_basic_auth').closest('.form-group').show();
        $('#id_dynamicdns_domain').closest('.form-group').show();
        $('#id_dynamicdns_user').closest('.form-group').show();
        $('#id_dynamicdns_secret').closest('.form-group').show();
        $('#id_showpw').closest('.form-group').show();
        $('#id_dynamicdns_ipurl').closest('.form-group').show();
    }
})(jQuery);
