  {{ service.name }}: {{ service.is_enabled }}<br>
  <a href="{% url 'vault:enable_service' service.name %}">enable</a>
  <a href="{% url 'vault:disable_service' service.name %}">disable</a>
  <br><br>

