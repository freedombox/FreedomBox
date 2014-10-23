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

{# use a variable to 'cache' the result of app.is_enabled #}
{% with is_enabled=app.is_enabled %}


<div class="panel panel-default {% if is_enabled %} enabled {% endif %}">

    <div class="panel-heading">
      {% block app-header %}
        <span class='appname'>
          {% block appname %}
            {% if app.url and is_enabled %}
              <a href="{{ app.url }}">{{ app.name|capfirst }}</a>
            {% else %}
              {{ app.name|capfirst }}
            {% endif %}
          {% endblock %}
        </span>

        <div class="btn-group pull-right">
          <button type="button" data-toggle="dropdown" class="btn btn-xs
                {% if is_enabled %}
                  btn-primary
                {% else %}
                  btn-default
                {% endif %}
                  dropdown-toggle">
            {% if is_enabled %}
              enabled
            {% else %}
              disabled
            {% endif %}
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">

            {% if is_enabled %}
              <li class="active"><a href="#">enable</a></li>
              <li>
                <a href="{% url 'dashboard:disable_app' app.name %}"
                   class="show-spinner">
                  disable
                </a>
              </li>
            {% else %}
              <li>
                <a href="{% url 'dashboard:enable_app' app.name %}"
                   class="show-spinner">
                  enable
                </a>
              </li>
              <li class="active"><a href="#">disable</a></li>
            {% endif %}

          </ul>
        </div>
      {% endblock %}
    </div>

    <div class="panel-body">
      {% block app-body %}
        {{ app.description }}
      {% endblock %}
    </div>

  </div>
{% endwith %}
