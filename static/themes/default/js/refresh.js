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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Refresh the page once in n seconds
async function refresh(ms) {
    await sleep(3000);
    // Refresh the page without resubmitting the POST data.
    window.location = window.location.href;
}

refresh();
