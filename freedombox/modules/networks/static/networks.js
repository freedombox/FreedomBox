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

document.addEventListener('DOMContentLoaded', () => {

    function ipRequired(required, ipVersion, fields) {
        const prefix = 'id_' + ipVersion + '_';
        for (var i = 0; i < fields.length; i++) {
            const element = document.getElementById(prefix + fields[i]);
            if (element) {
                element.required = required;
            }
        }
    }

    function ipReadOnly(readOnly, ipVersion, fields) {
        const prefix = 'id_' + ipVersion + '_';
        for (var i = 0; i < fields.length; i++) {
            const element = document.getElementById(prefix + fields[i]);
            if (element) {
                element.readOnly = readOnly;
                if (readOnly) {
                    element.value = "";
                    element.required = false;
                }
            }
        }
    }

    function onIpv4MethodChange() {
        const selected = document.querySelector("input[name=ipv4_method]:checked");
        if (selected && selected.value === "manual") {
            ipRequired(true, 'ipv4', ['address']);
            ipReadOnly(false, 'ipv4', ['address', 'netmask', 'gateway',
                'dns', 'second_dns'
            ]);
        } else if (selected && selected.value === "shared") {
            ipRequired(false, 'ipv4', ['address']);
            ipReadOnly(false, 'ipv4', ['address', 'netmask']);
            ipReadOnly(true, 'ipv4', ['gateway', 'dns', 'second_dns']);
        } else if (selected && selected.value === "auto") {
            ipReadOnly(true, 'ipv4', ['address', 'netmask', 'gateway']);
            ipReadOnly(false, 'ipv4', ['dns', 'second_dns']);
        } else {
            ipReadOnly(true, 'ipv4', ['address', 'netmask', 'gateway',
                'dns', 'second_dns'
            ]);
        }
    }

    function onIpv6MethodChange() {
        const selected = document.querySelector("input[name=ipv6_method]:checked");
        if (selected && selected.value === "manual") {
            ipRequired(true, 'ipv6', ['address', 'prefix']);
            ipReadOnly(false, 'ipv6', ['address', 'prefix', 'gateway',
                'dns', 'second_dns'
            ]);
        } else if (selected && (selected.value === "auto" ||
                                selected.value === "dhcp")) {
            ipReadOnly(true, 'ipv6', ['address', 'prefix', 'gateway']);
            ipReadOnly(false, 'ipv6', ['dns', 'second_dns']);
        } else {
            ipReadOnly(true, 'ipv6', ['address', 'prefix', 'gateway',
                'dns', 'second_dns'
            ]);
        }
    }

    document.querySelectorAll("input[name=ipv4_method]").forEach(element => {
        element.addEventListener('change', onIpv4MethodChange);
    });

    document.querySelectorAll("input[name=ipv6_method]").forEach(element => {
        element.addEventListener('change', onIpv6MethodChange);
    });

    onIpv4MethodChange();
    onIpv6MethodChange();

    const showPasswordElement = document.getElementById('id_show_password');
    if (showPasswordElement) {
        showPasswordElement.addEventListener('change', () => {
            // Changing type attribute from password to text is prevented by
            // most browsers. Making a new form field works.
            var newType = 'password';
            if (showPasswordElement.checked) {
                newType = 'text';
            }
            document.getElementById('id_password').type = newType;
        });
    }
});

// When there are validation errors on form elements, expand their parent
// collapsible so that the form element can be highlighted and an error tooltip
// can be show by the browser.
document.addEventListener('DOMContentLoaded', event => {
    const selector = '.form-connection input, .form-connection select';
    const inputElements = document.querySelectorAll(selector);
    inputElements.forEach(input =>
        input.addEventListener('invalid', onInvalidEvent)
    );
});

function onInvalidEvent(event) {
    const element = event.currentTarget;
    const parent = element.closest('.collapse');
    // Don't use .collapse(). Instead, expand all the sections with errors.
    parent.classList.add('show');
}
