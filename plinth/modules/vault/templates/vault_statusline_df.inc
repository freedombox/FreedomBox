{# statusline-item to show df of /home/fbx #}
{% with item.get_data as df %}
  Disk:
  <meter min="0" max="100" low="50" high="70" value="{{ df.used_percent }}"
         title="Used disk space">
    {{ df.available_gb|floatformat:1 }} GB free
  </meter>
{{ df.available_gb|floatformat:1 }} GB free
{% endwith %}
