<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemTypes_info">
<xsl:copy-of select="$systemTypes_model" />
<xsl:copy-of select="$systemTypes_methods" />
</xsl:variable>

<xsl:variable name="systemTypes_model"><![CDATA[
Description:
  A collection of valid system types
  
SystemTypes Properties:
  system_type - a system type resource]]>
<xsl:copy-of select="$systemType_model_properties" />
</xsl:variable>

<xsl:variable name="systemTypes_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <system_types>
        <system_type id="http://hostname/api/inventory/system_types/1/">
          ...
        </system_type>
        <system_type id="http://hostname/api/inventory/system_types/2/">
          ...
        </system_type>
      </system_types>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
