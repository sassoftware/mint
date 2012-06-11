<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="configuration_info">
<xsl:copy-of select="$configuration_model" />
<xsl:copy-of select="$configuration_methods" />
</xsl:variable>

<xsl:variable name="configuration_model"><![CDATA[
Description:
  The configuration data for a system in inventory]]>
<xsl:copy-of select="$configuration_model_properties" />
</xsl:variable>

<xsl:variable name="configuration_model_properties"><![CDATA[
Configuration Properties:
  All properties of this object are determined by the properties specified in the configuration_descriptor property of the system.]]>
</xsl:variable>

<xsl:variable name="configuration_methods"><![CDATA[
Methods: 
  GET:
    Authentication: admin
    Response Format:
      <configuration id="http://hostname/api/inventory/systems/1/configuration">
        ...
      </configuration>

  POST:
    Authentication: admin
    Required fields:
        The fields specified by the configuration_descriptor property of the system.
    Notes:
        Supported only when the inventoryConfigurationEnabled property of the api root is True.
    
  PUT:
    Authentication: admin
    Required fields:
        The fields specified by the configuration_descriptor property of this system's management interface.
    Notes:
        Supported only when the inventoryConfigurationEnabled property of the api root is True.
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
