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

const appForm = document.querySelector('#app-form');
const appToggleContainer = document.querySelector('#app-toggle-container');
const appToggleButton = document.querySelector('#app-toggle-button');
const appToggleInput = document.querySelector('#app-toggle-input');

if (appForm && appToggleButton && appToggleInput && appToggleContainer) {
  const onSubmit = (e) => {
    e.preventDefault;
    appToggleInput.checked = !appToggleInput.checked;
    appForm.submit();
  };

  appToggleButton.addEventListener('click', onSubmit);

  /**
   * if javascript is enabled, this script will run and show the toggle button
   */

  appToggleInput.parentElement.style.display = 'none';
  appToggleContainer.style.display = 'flex';

  /* A basic form has only three elements:
   *   1. An input tag with CSRF token
   *   2. A div with form elements
   *   3. A Submit button
   *
   * This kind of form can be completely hidden.
  */
  if (appForm.children.length === 3) {
    appForm.style.display = 'none';
    appForm.previousElementSibling.style.display = 'none';
  }
}
