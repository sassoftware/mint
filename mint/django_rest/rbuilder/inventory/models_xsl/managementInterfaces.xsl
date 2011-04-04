<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="managementInterfaces_info">
<xsl:copy-of select="$managementInterfaces_model" />
<xsl:copy-of select="$managementInterfaces_methods" />
</xsl:variable>

<xsl:variable name="managementInterfaces_model"><![CDATA[
Description:
  A collection of management interfaces
  
ManagementInterfaces Properties:
  management_interface - a management interface resource]]>
<xsl:copy-of select="$managementInterface_model_properties" />
</xsl:variable>

<xsl:variable name="managementInterfaces_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
