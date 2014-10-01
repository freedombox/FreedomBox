{# use a variable to 'cache' the result of app.is_enabled #}
{% with is_enabled=app.is_enabled %}

{% if is_enabled %}
  <div class="panel panel-success">
{% else %}
  <div class="panel panel-danger">
{% endif %}

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
                  btn-default dropdown-toggle">
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
