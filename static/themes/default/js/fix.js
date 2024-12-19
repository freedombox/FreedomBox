// SPDX-License-Identifier: AGPL-3.0-or-later
/*
  This file is part of FreedomBox.

  @licstart  The following is the entire license notice for the
  JavaScript code in this page.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  @licend  The above is the entire license notice
  for the JavaScript code in this page.
*/

// Workaround Debian bug #1087969. popper.js 2.x is needed for Bootstrap 5,
// however, the current version on in Debian is 1.x.
if (typeof(Popper.createPopper) === 'undefined') {
    window.Popper.createPopper = function(reference, popper, options) {
        if (options.modifiers.length == 1) {
            // Navbar dropdown
            options.modifiers = {
                'applyStyle': {'enabled': false}
            };
        } else {
            // Regular dropdown
            options.modifiers = {
                'flip': {'enabled': true},
                'offset': {'offset': 0},
                'preventOverflow': {'boundariesElement': 'scrollParent'}
            };
        }
        return new Popper(reference, popper, options);
    };
}
