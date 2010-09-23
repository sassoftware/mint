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

<xsl:variable name="zone_model_properties"><![CDATA[
Zone Properties:
  name - the zone name
  description - the zone description
  zone_id - the database id for the zone
  created_date - the date the zone was created (UTC)
  management_nodes - a collection of management nodes in this zone
  systems - a collection of systems that are managed by this zone]]>
</xsl:variable>

<xsl:variable name="zone_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <zone id="http://hostname/api/inventory/zones/1/">
         ...
       </zone>

  POST:
    not supported
    
  PUT:
    Authentication: admin
    
  DELETE:
    Authentication: admin]]>
</xsl:variable>

</xsl:stylesheet>
