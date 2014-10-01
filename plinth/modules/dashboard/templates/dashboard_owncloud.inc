{% extends "dashboard_app_default.inc" %}

{% block app-header %}
host: {{ request.get_host }}
{% endblock %}
