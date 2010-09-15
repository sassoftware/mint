<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="logHref.xsl"/>
<xsl:import href="systemStatesHref.xsl"/>
<xsl:import href="systemsHref.xsl"/>
<xsl:import href="zonesHref.xsl"/>

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
  zones - an entry point into inventory management zones collection]]>
<xsl:copy-of select="$eventTypesHrefModel" />
<xsl:copy-of select="$logHrefModel" />
<xsl:copy-of select="$systemStatesHrefModel" />
<xsl:copy-of select="$systemsHrefModel" />
<xsl:copy-of select="$zonesHrefModel" />
</xsl:variable>

<xsl:variable name="inventoryMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <inventory>
        <eventTypes href="http://hostname/api/inventory/eventTypes/"/>
        <log href="http://hostname/api/inventory/log/"/>
        <systemStates href="http://hostname/api/inventory/systemStates/"/>
        <systems href="http://hostname/api/inventory/systems/"/>
        <zones href="http://hostname/api/inventory/zones/"/>
      </inventory>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>