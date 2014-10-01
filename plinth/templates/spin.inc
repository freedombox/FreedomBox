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

{% load static %}
<script type="text/javascript" src="{% static 'theme/js/libs/spin.min.js' %}"></script>
<script type="text/javascript" src="{% static 'theme/js/spin.js' %}"></script>

<div id="spin-modal" class="modal fade" tabindex="-1" role="dialog"
     data-keyboard="false" data-backdrop="static">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header" style="text-align: center">
        <h3 class='title'></h3>
      </div>
      <div class="modal-body" >
        <div style="height:200px">
          <span id="spin-modal-center"
                style="position: absolute;display: block;top: 50%;left: 50%;">
          </span>
        </div>
      </div>
      <div class="modal-footer"></div>
    </div>
  </div>
</div>
