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

<xsl:variable name="job_model_properties"><![CDATA[   event_type - documentation missing
   job_id - the database id of the job
   job_state - the current state of the job
   job_uuid - a UUID for job tracking purposes
   status_code - the current status code of the job, typically an http status code
   status_detail - documentation missing
   status_text - the message associated with the current status
   time_created - the date the job was created (UTC)
   time_updated - the date the job was updated (UTC)]]>
</xsl:variable>

<xsl:variable name="job_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
