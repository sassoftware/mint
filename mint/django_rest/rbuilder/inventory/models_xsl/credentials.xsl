<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="credentials_info">
<xsl:copy-of select="$credentials_model" />
<xsl:copy-of select="$credentials_methods" />
</xsl:variable>

<xsl:variable name="credentials_model"><![CDATA[
Description:
  The credentials data for a system in inventory]]>
<xsl:copy-of select="$credentials_model_properties" />
</xsl:variable>

<xsl:variable name="credentials_model_properties"><![CDATA[
Credentials Properties:
  All properties of this object are determined by the properties specified in the credentials_descriptor property of this system's management interface.]]>
</xsl:variable>

<xsl:variable name="credentials_methods"><![CDATA[
Methods: 
  GET:
    Authentication: admin
    Response Format:
      <credentials id="http://hostname/api/inventory/systems/1/credentials">
        ...
      </credentials>

  POST:
    Authentication: admin
    Required fields:
        The fields specified by the credentials_descriptor property of this system's management interface.
    Supported:
        Only when the credentials_readonly property of this system's management interface is false.
    
  PUT:
    Authentication: admin
    Required fields:
        The fields specified by the credentials_descriptor property of this system's management interface.
    Notes:
        Supported only when the credentials_readonly property of this system's management interface is false.
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
