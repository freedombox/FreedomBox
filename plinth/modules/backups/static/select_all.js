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


// jQuery selector for the "select all" checkbox
var select_all = "#id_backups-selected_apps_0";

// Initialize the "select all" checkbox to checked
$(select_all).prop('checked', true);

/*
 * When there is a change on the "select all" checkbox,set the
 * checked property of all the checkboxes to the value of the
 * "select all" checkbox
 */
$(select_all).change(function() {
    $(":checkbox").prop('checked', $(this).prop("checked"));
});


$(':checkbox').change(function() {
    // If the rest of the checkbox items are checked check the "select all" checkbox as well
    if ($(':checkbox:checked').length == ($(':checkbox').length-1)) {
        $(select_all).prop('checked', true);
    }
    // Uncheck "select all" if one of the listed checkbox item is unchecked
    if (false == $(this).prop("checked")) {
        $(select_all).prop('checked', false);
    }
});
