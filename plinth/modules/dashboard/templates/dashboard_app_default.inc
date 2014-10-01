{# use a variable to 'cache' the result of app.is_enabled #}
{% with is_enabled=app.is_enabled %}

{% if is_enabled %}
  <div class="panel panel-success">
{% else %}
  <div class="panel panel-danger">
{% endif %}

    <div class="panel-heading">
      <span class='appname'>
        {% if app.url and is_enabled %}
          <a href="{{ app.url }}">{{ app.name }}</a>
        {% else %}
          {{ app.name }}
        {% endif %}
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
          <li {% if is_enabled %} class="active" {% endif %}>
            <a href="{% url 'dashboard:enable_app' app.name %}"
               class="show-spinner">
              enable
            </a>
          </li>
          <li {% if not is_enabled %} class="active" {% endif %}>
            <a href="{% url 'dashboard:disable_app' app.name %}"
               class="show-spinner">
              disable
            </a>
          </li>
        </ul>
      </div>

    </div>

    <div class="panel-body">
      {{ app.description }}
    </div>

  </div>
{% endwith %}
