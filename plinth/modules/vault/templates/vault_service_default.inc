{% if service.is_enabled %}
  <div class="panel panel-success">
    <div class="panel-heading">
        {{ service.name }} [running]
        <a href="{% url 'vault:disable_service' service.name %}" role="button"
           title="Stop {{ service.name }}"
           class="btn btn-xs btn-default pull-right">
          <span class="glyphicon glyphicon-off"></span>
        </a>
    </div>
{% else %}
  <div class="panel panel-danger">
    <div class="panel-heading">
      <h3 class="panel-title" title="{{ service.name }} is not running">
        {{ service.name }} [stopped]
        <a href="{% url 'vault:enable_service' service.name %}" role="button"
           title="Start {{ service.name }}"
           class="btn btn-xs btn-default pull-right">
          <span class="glyphicon glyphicon-play"></span>
        </a>
      </h3>
    </div>
{% endif %}
    <div class="panel-body">
      {{ service.description }}
    </div>
  </div>

