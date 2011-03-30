<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemLog_info">
<xsl:copy-of select="$systemLog_model" />
<xsl:copy-of select="$systemLog_methods" />
</xsl:variable>

<xsl:variable name="systemLog_model"><![CDATA[
Description:
  The inventory log data for the system]]>
<xsl:copy-of select="$systemLog_model_properties" />
</xsl:variable>

<xsl:variable name="systemLog_model_properties"><![CDATA[   system - a entry point to the system this log is for
   system_log_id - the database ID for the system log]]>
</xsl:variable>

<xsl:variable name="systemLog_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
