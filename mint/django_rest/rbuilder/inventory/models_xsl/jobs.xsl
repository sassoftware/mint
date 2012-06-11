<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="jobs_info">
<xsl:copy-of select="$jobs_model" />
<xsl:copy-of select="$jobs_methods" />
</xsl:variable>

<xsl:variable name="jobs_model"><![CDATA[
Description:
  A collection of jobs for the system
  
JobStates Properties:
  job - a job resource
  queued_jobs - an entry point into the collection of queued jobs for the system
  running_jobs - an entry point into the collection of running jobs for the system
  failed_jobs - an entry point into the collection of failed jobs for the system]]>
<xsl:copy-of select="$job_model_properties" />
</xsl:variable>

<xsl:variable name="jobs_methods"><![CDATA[
Methods: 
  GET:
    Authentication: anonymous
    Response Format:
      <jobs id="https://hostname/api/inventory/systems/1/jobs">
        <job id="https://hostname/api/inventory/jobs/1/">
          ...
        </job>
        <job id="https://hostname/api/inventory/jobs/2/">
          ...
        </job>
        <queued_jobs href="https://hostname/api/inventory/systems/1/job_states/1/jobs"/> 
        <completed_jobs href="https://hostname/api/inventory/systems/1/job_states/3/jobs"/> 
        <running_jobs href="https://hostname/api/inventory/systems/1/job_states/2/jobs"/> 
        <failed_jobs href="https://hostname/api/inventory/systems/1/job_states/4/jobs"/> 
      </jobs>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
