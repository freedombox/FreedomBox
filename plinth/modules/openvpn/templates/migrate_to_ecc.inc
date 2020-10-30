{% load i18n %}

<hr/>

<h3>{% trans "Migrate to ECC" %}</h3>

<p>
  {% blocktrans trimmed %}
    Your OpenVPN installation is currently using RSA. Switching to the
    modern Elliptic Curve Cryptography improves speed of establishing a
    connection and security. This operation is irreversible. It should only take
    a few minutes on most single board computers.
  {% endblocktrans %}
</p>

<p>
  {% blocktrans trimmed %}
    Existing client profiles will be invalidated by this operation. All
    OpenVPN users on {{ box_name }} should download their new profiles. OpenVPN
    clients compatible with ECC should be used to connect to this server.
  {% endblocktrans %}
</p>

<p>
  {% blocktrans trimmed %}
    All new installations of OpenVPN on {{ box_name }} will
    use ECC by default. We recommend migrating as soon as possible.
  {% endblocktrans %}
</p>

<form class="form form-ecc" method="post"
      action="{% url 'openvpn:ecc' %}">
  {% csrf_token %}

  <input type="submit" class="btn btn-primary"
        value="{% trans "Migrate" %}"/>
</form>
