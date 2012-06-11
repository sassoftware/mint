<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="job_info">
<xsl:copy-of select="$job_model" />
<xsl:copy-of select="$job_methods" />
</xsl:variable>

<xsl:variable name="job_model"><![CDATA[
Description:
  A job resource]]>
<xsl:copy-of select="$job_model_properties" />
</xsl:variable>

<xsl:variable name="job_model_properties"><![CDATA[
EventType Properties:
  job_id - the database id of the job
  status_code - the current status code of the job, typically an http status code
  status_text - the message associated with the current status
  job_state - the current state of the job
  job_type - the job type
  time_created - the date the job was created (UTC)
  systems - a collection of system resources impacted by this job
  job_uuid - a UUID for job tracking purposes
  job_description - a description of the job]]>
</xsl:variable>

<xsl:variable name="job_methods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
       <job id="http://hostname/api/inventory/jobs/1/">
         ...
       </job>
      
  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
