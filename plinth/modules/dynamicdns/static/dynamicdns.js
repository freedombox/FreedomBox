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
    const NOIP = 'https://<User>:<Pass>@dynupdate.no-ip.com/nic/update?' +
        'hostname=<Domain>';
    const FREEDNS = 'https://freedns.afraid.org/dynamic/update.php?' +
        '_YOURAPIKEYHERE_';

    document.getElementById('id_service_type').addEventListener('change', () => {
        setMode();

        const service_type = document.getElementById('id_service_type').value;
        if (service_type === "noip.com") {
            document.getElementById('id_update_url').value = NOIP;
        } else if (service_type === "freedns.afraid.org") {
            document.getElementById('id_update_url').value = FREEDNS;
        } else {  // GnuDIP and other
            document.getElementById('id_update_url').value = '';
        }
    });

    document.getElementById('id_show_password').addEventListener('change', () => {
        if (document.getElementById('id_show_password').checked) {
            document.getElementById('id_password').type = 'text';
        } else {
            document.getElementById('id_password').type = 'password';
        }
    });

    function setMode() {
        const service_type = document.getElementById('id_service_type').value;
        if (service_type === "gnudip") {
            setGnudipMode();
        } else {
            setUpdateUrlMode();
        }
    }

    function setGnudipMode() {
        document.querySelectorAll('.form-group').forEach((element) => {
            element.style.display = 'block';
        });
        document.getElementById('id_update_url').closest('.form-group').style.display = 'none';
        document.getElementById('id_disable_ssl_cert_check').closest('.form-group').style.display = 'none';
        document.getElementById('id_use_http_basic_auth').closest('.form-group').style.display = 'none';
        document.getElementById('id_use_ipv6').closest('.form-group').style.display = 'none';
        document.getElementById('id_server').closest('.form-group').style.display = 'block';
    }

    function setUpdateUrlMode() {
        document.getElementById('id_update_url').closest('.form-group').style.display = 'block';
        document.getElementById('id_disable_ssl_cert_check').closest('.form-group').style.display = 'block';
        document.getElementById('id_use_http_basic_auth').closest('.form-group').style.display = 'block';
        document.getElementById('id_use_ipv6').closest('.form-group').style.display = 'block';
        document.getElementById('id_server').closest('.form-group').style.display = 'none';
    }

    setMode();
});
