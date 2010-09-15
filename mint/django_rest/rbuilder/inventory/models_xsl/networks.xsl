<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systemsHref.xsl"/>

<xsl:variable name="networksInfo">
<xsl:copy-of select="$networksModel" />
<xsl:copy-of select="$networksMethods" />
</xsl:variable>

<xsl:variable name="networksModel"><![CDATA[
Description:
  A collection of networks attached to systems in inventory
  
Networks Properties:
  systems - an entry point into system inventory
  network - a network resource]]>
<xsl:copy-of select="$systemsHrefModel" />
<xsl:copy-of select="$networkModelProperties" />
</xsl:variable>

<xsl:variable name="networksMethods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <networks>
        <systems href="http://hostname/api/inventory/systems/"/>
        <network id="http://hostname/api/inventory/networks/1/">
          ...
        </network>
        <network id="http://hostname/api/inventory/networks/2/">
          ...
        </network>
      </networks>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>