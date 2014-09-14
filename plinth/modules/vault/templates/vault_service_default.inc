{% if service.is_enabled %}
  <div class="panel panel-success">
    <div class="panel-heading">
      <h3 class="panel-title" title="{{ service.name }} is not running">
        {{ service.name }}
      </h3>
    </div>
{% else %}
  <div class="panel panel-warning">
    <div class="panel-heading">
      <h3 class="panel-title" title="{{ service.name }} is running">
        {{ service.name }}
      </h3>
    </div>
{% endif %}
  <div class="panel-body">
    {{ service.description }}<br>
    <a href="{% url 'vault:enable_service' service.name %}">enable</a>
    <a href="{% url 'vault:disable_service' service.name %}">disable</a>
  </div>
</div>

