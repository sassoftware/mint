<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systems.xsl"/>

<xsl:variable name="management_node_info">
<xsl:copy-of select="$management_node_model" />
<xsl:copy-of select="$management_node_methods" />
</xsl:variable>

<xsl:variable name="management_node_model"><![CDATA[
Description:
  A management node in inventory.]]>
<xsl:copy-of select="$management_node_model_properties" />
</xsl:variable>

<xsl:variable name="management_node_model_properties"><![CDATA[
ManagementNode Properties (extends System resource):]]>
<xsl:copy-of select="$system_model_properties_no_description" /><![CDATA[   local - whether or not this management node is local to the rBuilder
   system_ptr - a link to the management node's underlying system
   zone - the zone the management node lives in
   node_jid - the Jabber ID the management node is using]]>
</xsl:variable>

<xsl:variable name="management_node_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <management_node id="http://hostname/api/inventory/management_nodes/1/">
         ...
       </management_node>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
