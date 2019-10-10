<?xml version="1.0" encoding="UTF-8"?>
<!--
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
-->
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Set output method to text -->
  <xsl:output method="text"/>

  <!-- Process and ignore all nodes by default -->
  <xsl:template match="@*|node()">
    <xsl:apply-templates select="@*|node()"/>
  </xsl:template>

  <!-- Output URLs from imagedata nodes -->
  <xsl:template match="imagedata">
    <xsl:call-template name="filename">
      <xsl:with-param name="path" select="@fileref"/>
    </xsl:call-template>
    <xsl:text> "</xsl:text>
    <xsl:value-of select="@fileref"/>
    <xsl:text>"&#010;</xsl:text>
  </xsl:template>

  <!-- Output just the filename from a URL -->
  <xsl:template match="@fileref[parent::imagedata]">
    <xsl:attribute name="fileref">
        <xsl:call-template name="filename">
          <xsl:with-param name="path" select="."/>
        </xsl:call-template>
    </xsl:attribute>
  </xsl:template>

  <xsl:template name="filename">
    <xsl:param name="path"/>
    <xsl:choose>
      <xsl:when test="contains($path, 'target=')">
        <xsl:value-of select="substring-after($path, 'target=')"/>
      </xsl:when>
      <xsl:when test="not(contains($path, '/'))">
        <xsl:value-of select="$path"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="filename">
          <xsl:with-param name="path" select="substring-after($path, '/')"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
