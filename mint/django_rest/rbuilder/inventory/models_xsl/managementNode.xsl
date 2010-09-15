<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systems.xsl"/>

<xsl:variable name="managementNodeInfo">
<xsl:copy-of select="$managementNodeModel" />
<xsl:copy-of select="$managementNodeMethods" />
</xsl:variable>

<xsl:variable name="managementNodeModel"><![CDATA[
Description:
  A management node in inventory.]]>
<xsl:copy-of select="$managementNodeModelProperties" />
</xsl:variable>

<xsl:variable name="managementNodeModelProperties"><![CDATA[
ManagementNode Properties (extends System resource):]]><xsl:copy-of select="$systemModelPropertiesNoDescription" /><![CDATA[  local - whether or not this management node is local to the rBuilder
  systemPtr - a link to the management node's underlying system
  zone - the zone the management node lives in
  nodeJid - the Jabber ID the management node is using]]>
</xsl:variable>

<xsl:variable name="managementNodeMethods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <managementNode id="http://hostname/api/inventory/managementNodes/1/">
         ...
       </managementNode>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>