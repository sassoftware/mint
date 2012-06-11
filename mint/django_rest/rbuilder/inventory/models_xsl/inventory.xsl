<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="systemTypesHref.xsl"/>
<xsl:import href="logHref.xsl"/>
<xsl:import href="systemStatesHref.xsl"/>
<xsl:import href="systemsHref.xsl"/>
<xsl:import href="infrastructureSystemsHref.xsl"/>
<xsl:import href="inventorySystemsHref.xsl"/>
<xsl:import href="managementInterfacesHref.xsl"/>
<xsl:import href="jobStatesHref.xsl"/>
<xsl:import href="zonesHref.xsl"/>
<xsl:import href="managementNodesHref.xsl"/>
<xsl:import href="networksHref.xsl"/>

<xsl:variable name="inventory_info">
<xsl:copy-of select="$inventory_model" />
<xsl:copy-of select="$inventory_methods" />
</xsl:variable>

<xsl:variable name="inventory_model"><![CDATA[
Description:
  A list of the entry points into the inventory API
  
Inventory Properties:
  event_types - an entry point into the inventory events collection
  log - an entry point into inventory logging
  system_types - an entry point into the inventory system types collection
  system_states - an entry point into the inventory system states collection
  systems - an entry point into the collection of all systems (all systems in inventory_systems and infrastructure systems combined)
  inventory_systems - an entry point into the collection of inventory systems (all systems visible in the UI under Systems)
  infrastructure_systems - an entry point into the collection of infrastructure systems (all systems visible in the UI under Infrastructure)
  management_interfaces - an entry point into the collection of management interfaces (CIM, WMI, etc.)
  job_states -  an entry point into the inventory job states collection
  zones - an entry point into the inventory management zones collection
  management_nodes - an entry point into the inventory management nodes collection (rPath Update Services)
  networks - an entry point into the inventory system networks collection]]>
<xsl:copy-of select="$event_types_href_model" />
<xsl:copy-of select="$log_href_model" />
<xsl:copy-of select="$system_types_href_model" />
<xsl:copy-of select="$system_states_href_model" />
<xsl:copy-of select="$systems_href_model" />
<xsl:copy-of select="$inventory_systems_href_model" />
<xsl:copy-of select="$infrastructure_systems_href_model" />
<xsl:copy-of select="$management_interfaces_href_model" />
<xsl:copy-of select="$job_states_href_model" />
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
