<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="jobState_info">
<xsl:copy-of select="$jobState_model" />
<xsl:copy-of select="$jobState_methods" />
</xsl:variable>

<xsl:variable name="jobState_model"><![CDATA[
Description:
  A job state in inventory]]>
<xsl:copy-of select="$jobState_model_properties" />
</xsl:variable>

<xsl:variable name="jobState_model_properties"><![CDATA[
JobState Properties:
  job_state_id - the database ID for the job state
  name - the name of the job state
  jobs - an entry point into the collection of jobs in this job state]]>
</xsl:variable>

<xsl:variable name="jobState_methods"><![CDATA[
Methods: 
  GET:
    Authentication: anonymous
    Response Format:
      <job_state id="http://hostname/api/inventory/job_states/1/">
        ...
      </job_state>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
