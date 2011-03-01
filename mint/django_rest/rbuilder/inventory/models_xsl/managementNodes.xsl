<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="managementNode.xsl"/>

<xsl:variable name="management_nodes_info">
<xsl:copy-of select="$management_nodes_model" />
<xsl:copy-of select="$management_nodes_methods" />
</xsl:variable>

<xsl:variable name="inventory_management_nodes_info">
<xsl:copy-of select="$management_nodes_model" />
<xsl:copy-of select="$inventory_management_nodes_methods" />
</xsl:variable>


<xsl:variable name="management_nodes_model"><![CDATA[
Description:
  A collection of management nodes available to inventory systems
  
ManagementNodes Properties:
  management_node - a management node resource]]>
<xsl:copy-of select="$management_node_model_properties" />
</xsl:variable>

<xsl:variable name="management_nodes_methods"><![CDATA[@@METHODS-viewName1@@]]>
</xsl:variable>

<xsl:variable name="inventory_management_nodes_methods"><![CDATA[@@METHODS-viewName2@@]]>
</xsl:variable>

</xsl:stylesheet>
