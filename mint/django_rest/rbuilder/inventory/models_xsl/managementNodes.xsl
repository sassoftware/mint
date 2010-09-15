<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="managementNode.xsl"/>

<xsl:variable name="managementNodesInfo">
<xsl:copy-of select="$managementNodesModel" />
<xsl:copy-of select="$managementNodesMethods" />
</xsl:variable>

<xsl:variable name="managementNodesModel"><![CDATA[
Description:
  A collection of management nodes available to inventory systems
  
ManagementNodes Properties:
  managementNode - a management node resource]]>
<xsl:copy-of select="$managementNodeModelProperties" />
</xsl:variable>

<xsl:variable name="managementNodesMethods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <managementNodes>
        <managementNode id="http://hostname/api/inventory/managementNodes/1/">
          ...
        </managementNode>
        <managementNode id="http://hostname/api/inventory/managementNodes/2/">
          ...
        </managementNode>
      </managementNodes>
      
  POST:
    Authentication: admin
    Required Fields:
      name
      zone
    Example:
      <managementNode>
        <name>East Datacenter Node 1</name>
        <description>Management node 1 for east datacenter</description>
        <zone href="http://hostname/api/inventory/zones/1/">
      </managementNode>
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>