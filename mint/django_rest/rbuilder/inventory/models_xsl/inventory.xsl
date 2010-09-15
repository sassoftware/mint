<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="logHref.xsl"/>
<xsl:import href="systemStatesHref.xsl"/>
<xsl:import href="systemsHref.xsl"/>
<xsl:import href="zonesHref.xsl"/>
<xsl:import href="managementNodesHref.xsl"/>
<xsl:import href="networksHref.xsl"/>

<xsl:variable name="inventoryInfo">
<xsl:copy-of select="$inventoryModel" />
<xsl:copy-of select="$inventoryMethods" />
</xsl:variable>

<xsl:variable name="inventoryModel"><![CDATA[
Description:
  A node listing the entry points into the inventory API
  
Inventory Properties:
  eventTypes - an entry point into inventory event types
  log - an entry point into inventory logging
  systemStates - an entry point into the inventory system states collection
  systems - an entry point into the inventory systems collection
  zones - an entry point into inventory management zones collection
  managementNodes - an entry point into inventory management nodes collection
  networks - an entry point into inventory system networks collection]]>
<xsl:copy-of select="$eventTypesHrefModel" />
<xsl:copy-of select="$logHrefModel" />
<xsl:copy-of select="$systemStatesHrefModel" />
<xsl:copy-of select="$systemsHrefModel" />
<xsl:copy-of select="$zonesHrefModel" />
<xsl:copy-of select="$managementNodesHrefModel" />
<xsl:copy-of select="$networksHrefModel" />
</xsl:variable>

<xsl:variable name="inventoryMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <inventory>
        ...
      </inventory>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>