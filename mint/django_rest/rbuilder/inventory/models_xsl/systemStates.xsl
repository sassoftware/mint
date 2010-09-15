<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systemState.xsl"/>

<xsl:variable name="systemStatesInfo">
<xsl:copy-of select="$systemStatesModel" />
<xsl:copy-of select="$systemStatesMethods" />
</xsl:variable>

<xsl:variable name="systemStatesModel"><![CDATA[
Description:
  A collection of states applicable to systems in inventory
  
SystemStates Properties:
  systemState - a system state resource]]>
<xsl:copy-of select="$systemStateModelProperties" />
</xsl:variable>

<xsl:variable name="systemStatesMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <systemStates> 
        <systemState id="http://hostname/api/inventory/systemStates/1/">
          ...
        </systemState>
        <systemState id="http://hostname/api/inventory/systemStates/2/">
          ...
        </systemState>
      </systemStates>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>