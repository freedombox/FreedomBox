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
    const keyAuth = document.getElementById('id_ssh_auth_type_key');
    const passwordAuth = document.getElementById('id_ssh_auth_type_password');
    const sshPasswordField = document.getElementById('id_ssh_password');
    const encryptionType = document.getElementById('id_encryption');
    const encryptionPassphraseField = document.getElementById('id_encryption_passphrase');
    const encryptionConfirmPassphraseField = document.getElementById('id_confirm_encryption_passphrase');

    function handleAuthTypeChange() {
        if (keyAuth.checked) {
            sshPasswordField.value = "";
            sshPasswordField.disabled = true;
        } else {
            sshPasswordField.disabled = false;
        }
    }

    function handleEncryptionTypeChange() {
        if (encryptionType.value === "repokey") {
            encryptionPassphraseField.disabled = false;
            encryptionConfirmPassphraseField.disabled = false;
        } else {
            encryptionPassphraseField.value = "";
            encryptionPassphraseField.disabled = true;
            encryptionConfirmPassphraseField.value = "";
            encryptionConfirmPassphraseField.disabled = true;
        }
    }

    keyAuth.addEventListener('change', handleAuthTypeChange);
    passwordAuth.addEventListener('change', handleAuthTypeChange);
    encryptionType.addEventListener('change', handleEncryptionTypeChange);

    handleAuthTypeChange();
    handleEncryptionTypeChange();
});
