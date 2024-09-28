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

jQuery(function($) {

    function ip_required(required, ip_version, fields) {
        var prefix = '#id_' + ip_version + '_';
        for (var i = 0; i < fields.length; i++) {
            $(prefix + fields[i]).prop("required", required);
        }
    }

    function ip_readonly(readonly, ip_version, fields) {
        var prefix = '#id_' + ip_version + '_';
        for (var i = 0; i < fields.length; i++) {
            $(prefix + fields[i]).prop("readOnly", readonly);
            if (readonly) {
                $(prefix + fields[i]).val("");
                $(prefix + fields[i]).prop("required", false);
            }
        }
    }

    function on_ipv4_method_change() {
        var selected = $("input[name=ipv4_method]:checked");
        if (selected.prop("value") == "manual") {
            ip_required(true, 'ipv4', ['address']);
            ip_readonly(false, 'ipv4', ['address', 'netmask', 'gateway',
                'dns', 'second_dns'
            ]);
        } else if (selected.prop("value") == "shared") {
            ip_required(false, 'ipv4', ['address']);
            ip_readonly(false, 'ipv4', ['address', 'netmask']);
            ip_readonly(true, 'ipv4', ['gateway', 'dns', 'second_dns']);
        } else if (selected.prop("value") == "auto") {
            ip_readonly(true, 'ipv4', ['address', 'netmask', 'gateway']);
            ip_readonly(false, 'ipv4', ['dns', 'second_dns']);
        } else {
            ip_readonly(true, 'ipv4', ['address', 'netmask', 'gateway',
                'dns', 'second_dns'
            ]);
        }
    }

    function on_ipv6_method_change() {
        var selected = $("input[name=ipv6_method]:checked");
        if (selected.prop("value") == "manual") {
            ip_required(true, 'ipv6', ['address', 'prefix']);
            ip_readonly(false, 'ipv6', ['address', 'prefix', 'gateway',
                'dns', 'second_dns'
            ]);
        } else if (selected.prop("value") == "auto" ||
            $("#id_ipv6_method").prop("value") == "dhcp") {
            ip_readonly(true, 'ipv6', ['address', 'prefix', 'gateway']);
            ip_readonly(false, 'ipv6', ['dns', 'second_dns']);
        } else {
            ip_readonly(true, 'ipv6', ['address', 'prefix', 'gateway',
                'dns', 'second_dns'
            ]);
        }
    }

    $("#id_name").focus();

    $("input[name=ipv4_method]").change(on_ipv4_method_change).change();
    $("input[name=ipv6_method]").change(on_ipv6_method_change).change();

    $('#id_show_password').change(function() {
        // Changing type attribute from password to text is prevented by
        // most browsers. Making a new form field works.
        new_type = 'password';
        if ($('#id_show_password').prop('checked'))
            new_type = 'text';

        $('#id_password').replaceWith(
            $('#id_password').clone().attr('type', new_type));
    });

});

// When there are validation errors on form elements, expand their parent
// collapsible so that the form element can be highlighted and an error tooltip
// can be show by the browser.
document.addEventListener('DOMContentLoaded', event => {
    const selector = '.form-connection input, .form-connection select';
    const input_elements = document.querySelectorAll(selector);
    input_elements.forEach(input =>
        input.addEventListener('invalid', on_invalid_event)
    );
});

function on_invalid_event(event) {
    const element = event.target;
    const parent = element.closest('.collapse');
    // Don't use .collapse(). Instead, expand all the sections with errors.
    parent.classList.add('show');
}
