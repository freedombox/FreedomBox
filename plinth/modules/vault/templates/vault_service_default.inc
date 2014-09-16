{# use a variable to 'cache' the result of service.is_enabled #}
{% with is_enabled=service.is_enabled %}

{% if is_enabled %}
  <div class="panel panel-success">
{% else %}
  <div class="panel panel-danger">
{% endif %}

    <div class="panel-heading">
      <span class='appname'>
        {% if service.url and is_enabled %}
          <a href="{{ service.url }}">{{ service.name }}</a>
        {% else %}
          {{ service.name }}
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
            <a href="{% url 'vault:enable_service' service.name %}"
               class="show-spinner">
              enable
            </a>
          </li>
          <li {% if not is_enabled %} class="active" {% endif %}>
            <a href="{% url 'vault:disable_service' service.name %}"
               class="show-spinner">
              disable
            </a>
          </li>
        </ul>
      </div>

    </div>

    <div class="panel-body">
      {{ service.description }}
    </div>

  </div>
{% endwith %}
