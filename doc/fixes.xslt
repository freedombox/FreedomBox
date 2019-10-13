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

  <!-- Set output format to Docbook -->
  <xsl:output
      method="xml"
      encoding="utf-8"
      indent="yes"
      doctype-public="-//OASIS//DTD DocBook XML V4.4//EN"
      doctype-system="http://www.docbook.org/xml/4.4/docbookx.dtd"/>

  <!-- Copy all nodes and attributes by default -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Replace / in title with a space -->
  <xsl:template match="articleinfo/title/text()">
    <xsl:call-template name="clean-title">
      <xsl:with-param name="title" select="."/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="clean-title">
    <xsl:param name="title"/>
    <xsl:choose>
      <xsl:when test="contains($title, '/')">
        <!-- Skip copying the language code -->
        <xsl:choose>
          <xsl:when test="not(string-length(substring-before($title, '/'))=2)
                          and
                          not(string-length(substring-before($title, '/'))=5 and contains(substring-before($title, '/'), '-'))">
            <xsl:value-of select="substring-before($title, '/')"/>
            <xsl:text> </xsl:text>
          </xsl:when>
        </xsl:choose>
        <xsl:call-template name="clean-title">
          <xsl:with-param name="title" select="substring-after($title, '/')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$title"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Remove revision history -->
  <xsl:template match="revhistory"/>

  <!-- Convert all image dimensions from pixels to points -->
  <xsl:template match="@width[parent::imagedata]|@depth[parent::imagedata]">
    <xsl:attribute name="{name()}">
      <xsl:value-of select=". div 2"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:template>

  <!-- Convert all image source URLs to relative paths -->
  <xsl:template match="@fileref[parent::imagedata]">
    <xsl:attribute name="fileref">
      <xsl:text>images/</xsl:text>
      <xsl:call-template name="filename">
        <xsl:with-param name="path" select="."/>
      </xsl:call-template>
    </xsl:attribute>
  </xsl:template>

  <!-- Output just the filename from a URL -->
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

  <!-- Fix incorrectly output wiki links -->
  <xsl:template match="@url[parent::ulink]">
    <xsl:attribute name="url">
      <xsl:choose>
        <xsl:when test="contains(., 'FreedomBox/Manual/')">
          <xsl:value-of select="substring-before(., 'FreedomBox/Manual/')"/>
          <xsl:value-of select="substring-after(., 'FreedomBox/Manual/')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="."/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
  </xsl:template>

</xsl:stylesheet>
