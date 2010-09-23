<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="logHref.xsl"/>
<xsl:import href="systemStatesHref.xsl"/>
<xsl:import href="systemsHref.xsl"/>
<xsl:import href="zonesHref.xsl"/>
<xsl:import href="managementNodesHref.xsl"/>
<xsl:import href="networksHref.xsl"/>

<xsl:variable name="inventory_info">
<xsl:copy-of select="$inventory_model" />
<xsl:copy-of select="$inventory_methods" />
</xsl:variable>

<xsl:variable name="inventory_model"><![CDATA[
Description:
  A node listing the entry points into the inventory API
  
Inventory Properties:
  event_types - an entry point into inventory event types
  log - an entry point into inventory logging
  system_states - an entry point into the inventory system states collection
  systems - an entry point into the inventory systems collection
  zones - an entry point into inventory management zones collection
  management_nodes - an entry point into inventory management nodes collection
  networks - an entry point into inventory system networks collection]]>
<xsl:copy-of select="$event_types_href_model" />
<xsl:copy-of select="$log_href_model" />
<xsl:copy-of select="$system_states_href_model" />
<xsl:copy-of select="$systems_href_model" />
<xsl:copy-of select="$zones_href_model" />
<xsl:copy-of select="$management_nodes_href_model" />
<xsl:copy-of select="$networks_href_model" />
</xsl:variable>

<xsl:variable name="inventory_methods"><![CDATA[
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
