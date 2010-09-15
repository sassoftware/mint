<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemStateInfo">
<xsl:copy-of select="$systemStateModel" />
<xsl:copy-of select="$systemStateMethods" />
</xsl:variable>

<xsl:variable name="systemStateModel"><![CDATA[
Description:
  A system state resource]]>
<xsl:copy-of select="$systemStateModelProperties" />
</xsl:variable>

<xsl:variable name="systemStateModelProperties"><![CDATA[
SystemState Properties:
  name - the state name
  description - the state description
  systemStateId - the database id for the state
  createdDate - the date the state was created (UTC)]]>
</xsl:variable>

<xsl:variable name="systemStateMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
       <systemState id="http://hostname/api/inventory/systemStates/1/">
         ...
       </systemState>
      
  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>