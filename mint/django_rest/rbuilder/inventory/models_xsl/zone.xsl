<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="zone_info">
<xsl:copy-of select="$zone_model" />
<xsl:copy-of select="$zone_methods" />
</xsl:variable>

<xsl:variable name="zone_model"><![CDATA[
Description:
  A zone in inventory]]>
<xsl:copy-of select="$zone_model_properties" />
</xsl:variable>

<xsl:variable name="zone_model_properties"><![CDATA[   created_date - the date the zone was created (UTC)
   description - the zone description
   name - the zone name
   zone_id - the database id for the zone]]>
</xsl:variable>

<xsl:variable name="zone_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
