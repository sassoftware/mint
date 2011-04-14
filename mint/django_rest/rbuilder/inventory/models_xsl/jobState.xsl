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

<xsl:variable name="jobState_model_properties"><![CDATA[   job_state_id - the database ID for the job state
   name - the name of the job state]]>
</xsl:variable>

<xsl:variable name="jobState_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
