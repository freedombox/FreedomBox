{# statusline-item to show df of /home/fbx #}
{% with item.get_data as df %}
  total: {{ df.total }}
  used: {{ df.used }}
  available: {{ df.available }}
{% endwith %}
