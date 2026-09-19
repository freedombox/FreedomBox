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
    const sharingGroups = document.getElementById('id_sharing-groups').closest('.form-group');
    const isPublic = document.getElementById('id_sharing-is_public');

    if (isPublic.checked) {
        sharingGroups.style.display = 'none';
    }

    isPublic.addEventListener('change', (event) => {
        if (event.currentTarget.checked) {
            sharingGroups.style.display = 'none';
        } else {
            sharingGroups.style.display = '';
        }
    });
});
