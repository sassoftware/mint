<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="managementInterface_info">
<xsl:copy-of select="$managementInterface_model" />
<xsl:copy-of select="$managementInterface_methods" />
</xsl:variable>

<xsl:variable name="managementInterface_model"><![CDATA[
Description:
  A management interface in inventory]]>
<xsl:copy-of select="$managementInterface_model_properties" />
</xsl:variable>

<xsl:variable name="managementInterface_model_properties"><![CDATA[   created_date - the date the management interface was added to inventory (UTC)
   credentials_descriptor - the descriptor of available fields to set credentials for the management interface
   credentials_readonly - whether or not the management interface has readonly credentials
   description - the description of the management interface
   management_interface_id - the database ID for the management interface
   name - the name of the management interface
   port - the port used by the management interface]]>
</xsl:variable>

<xsl:variable name="managementInterface_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
