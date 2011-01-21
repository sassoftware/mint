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

<xsl:variable name="managementInterface_model_properties"><![CDATA[
ManagementInterface Properties:
  management_interface_id - the database ID for the management interface
  name - the name of the management interface
  description - the description of the management interface
  created_date - "the date the management interface was added to inventory (UTC)
  port - the port used by the management interface
  credentials_descriptor - the descriptor of available fields to set credentials for the management interface
  credentials_readonly - whether or not the management interface has readonly credentials]]>
</xsl:variable>

<xsl:variable name="managementInterface_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <management_interface id="http://hostname/api/inventory/management_interfaces/1/">
        ...
      </management_interface>

  POST:
    not supported
    
  PUT:
    Authentication: admin
    Read-only fields:
        name
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
