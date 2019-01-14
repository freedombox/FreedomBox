{% comment %}
#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
{% endcomment %}

{% load i18n %}

<table class="table table-bordered table-condensed table-striped"
       id="archives-list">
  <thead>
    <tr>
      <th colspan="2">

        {% if repository.error %}
           <span class="fa fa-exclamation-triangle mount-error"
                 aria-hidden="true" title="{{ repository.error }}">
           </span>
        {% endif %}

        {{ repository.name }}

        {% if editable %}

          {% if repository.mounted %}

            <!-- With GET redirects, the browser URL points to the
                 redirected page (bad when reloading) - use POST instead.
            -->
            <form action="{% url 'backups:repository-umount' uuid %}" method="POST"
                  class="inline-block" >
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-default"
                     title="{% trans 'Unmount Location' %}">
               <span class="fa fa-eject" aria-hidden="true">
               </button>
            </form>

          {% else %}

            <form action="{% url 'backups:repository-mount' uuid %}" method="POST"
                  class="inline-block" >
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-default"
                     title="{% trans 'Mount Location' %}">
               <span class="fa fa-eye" aria-hidden="true">
               </button>
            </form>

          {% endif %}

          <a title="{% trans 'Remove Location. This will not delete the remote backup.' %}"
             role="button" class="repository-remove btn btn-sm btn-default"
             href="{% url 'backups:repository-remove' uuid %}">
             <span class="fa fa-trash" aria-hidden="true">
          </a>

        {% endif %}

      </th>
    </tr>
  </thead>

  <tbody>
    {% if repository.mounted %}

      {% for archive in repository.archives %}
        <tr id="archive-{{ archive.name }}" class="archive">
          <td class="archive-name">{{ archive.name }}</td>
          <td class="archive-operations">
            <a class="archive-export btn btn-sm btn-default" target="_blank"
               href="{% url 'backups:download' uuid archive.name %}">
              {% trans "Download" %}
            </a>
            <a class="archive-export btn btn-sm btn-default"
               href="{% url 'backups:restore-archive' uuid archive.name %}">
              {% trans "Restore" %}
            </a>
            <a class="archive-delete btn btn-sm btn-default"
               href="{% url 'backups:delete' uuid archive.name %}">
              <span class="fa fa-trash" aria-hidden="true">
              </span>
            </a>
          </td>
        </tr>
      {% endfor %}

      {% if not repository.error and not repository.archives %}
        <tr>
          <td>
            <p>{% trans 'No archives currently exist.' %}</p>
          </td>
        </tr>
      {% endif %}

    {% endif %}
  </tbody>
</table>
