<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="system_state_info">
<xsl:copy-of select="$system_state_model" />
<xsl:copy-of select="$system_state_methods" />
</xsl:variable>

<xsl:variable name="system_state_model"><![CDATA[
Description:
  A system state resource]]>
<xsl:copy-of select="$system_state_model_properties" />
</xsl:variable>

<xsl:variable name="system_state_model_properties"><![CDATA[
SystemState Properties:
  name - the state name
  description - the state description
  system_state_id - the database id for the state
  created_date - the date the state was created (UTC)]]>
</xsl:variable>

<xsl:variable name="system_state_methods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
       <system_state id="http://hostname/api/inventory/system_states/1/">
         ...
       </system_state>
      
  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>