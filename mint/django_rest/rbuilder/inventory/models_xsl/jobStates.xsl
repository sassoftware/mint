<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="jobStates_info">
<xsl:copy-of select="$jobStates_model" />
<xsl:copy-of select="$jobStates_methods" />
</xsl:variable>

<xsl:variable name="jobStates_model"><![CDATA[
Description:
  A collection of valid job states
  
JobStates Properties:
  job_state - a job state resource]]>
<xsl:copy-of select="$jobState_model_properties" />
</xsl:variable>

<xsl:variable name="jobStates_methods"><![CDATA[
Methods: 
  GET:
    Authentication: anonymous
    Response Format:
      <job_states>
        <job_state id="http://hostname/api/inventory/job_states/1/">
          ...
        </job_state>
        <job_state id="http://hostname/api/inventory/job_states/2/">
          ...
        </job_state>
      </job_states>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
