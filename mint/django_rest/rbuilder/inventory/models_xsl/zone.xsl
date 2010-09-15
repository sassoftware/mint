<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="zoneInfo">
<xsl:copy-of select="$zoneModel" />
<xsl:copy-of select="$zoneMethods" />
</xsl:variable>

<xsl:variable name="zoneModel"><![CDATA[
Description:
  A zone in inventory]]>
<xsl:copy-of select="$zoneModelProperties" />
</xsl:variable>

<xsl:variable name="zoneModelProperties"><![CDATA[
Zone Properties:
  name - the zone name
  description - the zone description
  zoneId - the database id for the zone
  createdDate - the date the zone was created (UTC)
  managementNodes - a collection of management nodes in this zone
  systems - a collection of systems that are managed by this zone]]>
</xsl:variable>

<xsl:variable name="zoneMethods"><![CDATA[
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