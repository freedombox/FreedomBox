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

document.addEventListener('DOMContentLoaded', (event) => {
    const form = document.querySelector('form.form-update');
    form.addEventListener('submit', onUserUpdateSubmit);

    const confirmDeleteButton = document.querySelector(
        '#user-delete-confirm-dialog button.confirm');
    confirmDeleteButton.addEventListener('click', () => {
        onUserDeleteConfirmed(form);
    });

    var deleteConfirmed = false;
    const modal = new bootstrap.Modal('#user-delete-confirm-dialog');

    // Show the confirmation dialog if the delete checkbox is selected
    function onUserUpdateSubmit(event) {
        const deleteUserCheckbox = document.getElementById('id_delete');
        if (!deleteUserCheckbox.checked) {
            return;
        }

        if (deleteConfirmed) { // Deletion is already confirmed
           deleteConfirmed = false;
           return;
        }

        event.preventDefault();
        modal.show();
    };

    // Submit the user edit form
    function onUserDeleteConfirmed(form) {
        deleteConfirmed = true;
        modal.hide();
        // Click instead of submit to disable the submission button
        form.querySelector('input[type=submit]').click();
    };
});
