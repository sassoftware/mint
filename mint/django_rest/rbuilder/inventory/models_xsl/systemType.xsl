<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemType_info">
<xsl:copy-of select="$systemType_model" />
<xsl:copy-of select="$systemType_methods" />
</xsl:variable>

<xsl:variable name="systemType_model"><![CDATA[
Description:
  A system type in inventory]]>
<xsl:copy-of select="$systemType_model_properties" />
</xsl:variable>

<xsl:variable name="systemType_model_properties"><![CDATA[
SystemType Properties:
  system_type_id - the database ID for the system type
  name - the name of the system type
  description - the description of the system type
  created_date - the date the system type was added to inventory (UTC)
  infrastructure - whether or not the system type is infrastructure
  creation_descriptor - the descriptor of available fields to create systems of this type]]>
</xsl:variable>

<xsl:variable name="systemType_methods"><![CDATA[
Methods: 
  GET:
    Authentication: anonymous
    Response Format:
      <system_type id="http://hostname/api/inventory/system_types/1/">
        ...
      </system_type>

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
