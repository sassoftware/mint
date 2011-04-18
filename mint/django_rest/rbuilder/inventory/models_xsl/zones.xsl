<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="zone.xsl"/>

<xsl:variable name="zones_info">
<xsl:copy-of select="$zones_model" />
<xsl:copy-of select="$zones_methods" />
</xsl:variable>

<xsl:variable name="zones_model"><![CDATA[
Description:
  A collection of management zones available to inventory systems
  
Zones Properties:
  zone - a zone resource]]>
<xsl:copy-of select="$zone_model_properties" />
</xsl:variable>

<xsl:variable name="zones_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
