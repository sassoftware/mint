<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systemState.xsl"/>

<xsl:variable name="system_states_info">
<xsl:copy-of select="$system_states_model" />
<xsl:copy-of select="$system_states_methods" />
</xsl:variable>

<xsl:variable name="system_states_model"><![CDATA[
Description:
  A collection of states applicable to systems in inventory
  
SystemStates Properties:
  system_state - a system state resource]]>
<xsl:copy-of select="$system_state_model_properties" />
</xsl:variable>

<xsl:variable name="system_states_methods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <system_states> 
        <system_state id="http://hostname/api/inventory/system_states/1/">
          ...
        </system_state>
        <system_state id="http://hostname/api/inventory/system_states/2/">
          ...
        </system_state>
      </system_states>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
