<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="managementNode.xsl"/>

<xsl:variable name="management_nodes_info">
<xsl:copy-of select="$management_nodes_model" />
<xsl:copy-of select="$management_nodes_methods" />
</xsl:variable>

<xsl:variable name="management_nodes_model"><![CDATA[
Description:
  A collection of management nodes available to inventory systems
  
ManagementNodes Properties:
  management_node - a management node resource]]>
<xsl:copy-of select="$management_node_model_properties" />
</xsl:variable>

<xsl:variable name="management_nodes_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <management_nodes>
        <management_node id="http://hostname/api/inventory/management_nodes/1/">
          ...
        </management_node>
        <management_node id="http://hostname/api/inventory/management_nodes/2/">
          ...
        </management_node>
      </management_nodes>
      
  POST:
    Authentication: admin
    Required Fields:
      name
      zone
    Example:
      <management_node>
        <name>East Datacenter Node 1</name>
        <description>Management node 1 for east datacenter</description>
        <zone href="http://hostname/api/inventory/zones/1/"/>
      </management_node>
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
