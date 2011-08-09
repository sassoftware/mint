<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="system.xsl"/>

<xsl:variable name="systems_info">
<xsl:copy-of select="$systems_model" />
<xsl:copy-of select="$systems_methods" />
</xsl:variable>

<xsl:variable name="systems_model"><![CDATA[
Description:
  A collection of systems in inventory
  
Systems Properties:
  event_types - an entry point into system inventory event types
  system - a system resource]]>
<xsl:copy-of select="$event_types_href_model" />
<xsl:copy-of select="$system_model_properties" />
<xsl:copy-of select="$system_model_dedup" />
</xsl:variable>

<xsl:variable name="systems_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
