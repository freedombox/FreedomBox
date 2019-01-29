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

function addSelectAll() {
    let ul = document.getElementById('id_backups-selected_apps');
    let li = document.createElement('li');

    let label = document.createElement('label');
    label.for = "select_all";

    let checkbox = document.createElement('input');
    checkbox.type = "checkbox";
    checkbox.checked = "checked";
    checkbox.id = "select-all";

    label.appendChild(checkbox);
    li.appendChild(label);

    ul.insertBefore(li, ul.childNodes[0]);
};

addSelectAll();

/*
 * When there is a change on the "select all" checkbox,set the
 * checked property of all the checkboxes to the value of the
 * "select all" checkbox
 */
$("#select-all").change(function() {
    $("[type=checkbox]").prop('checked', $(this).prop("checked"));
});


$('[type=checkbox]').change(function() {
    // If the rest of the checkbox items are checked check the "select all" checkbox as well
    if ($('[type=checkbox]:checked').length == ($('[type=checkbox]').length - 1)) {
        $("#select-all").prop('checked', true);
    }
    // Uncheck "select all" if one of the listed checkbox item is unchecked
    if (false == $(this).prop("checked")) {
        $("#select-all").prop('checked', false);
    }
});


