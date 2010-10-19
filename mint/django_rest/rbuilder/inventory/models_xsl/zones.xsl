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

<xsl:variable name="zones_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <zones>
        <zone id="http://hostname/api/inventory/zones/1/">
          ...
        </zone>
        <zone id="http://hostname/api/inventory/zones/2/">
          ...
        </zone>
      </zones>
      
  POST:
    Authentication: admin
    Required Fields:
      name
    Example:
      <zone>
        <name>East Datacenter</name>
        <description>Management zone for east datacenter</description>
      </zone>
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
