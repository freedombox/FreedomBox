{% comment %}
#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
{% endcomment %}

{# statusline-item to show df of /home/fbx #}
{% with item.get_data as df %}
  Disk:
    <div class="progress">
      <div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="{{ df.used_percent }}" aria-valuemin="0" aria-valuemax="100" style="width: {{ df.used_percent }}%;" title="{{ df.used_percent|floatformat }} % of your disk are used, you have {{ df.available_gb|floatformat }} GB left" >
        {{ df.used_percent|floatformat }}%
      </div>
    </div>
{% endwith %}
