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

<xsl:variable name="systemLog_model_properties"><![CDATA[
SystemLog Properties:
  system_log_id - the database ID for the system log
  system_log_entries - a collection of log entries for the system
  system - a entry point to the system this log is for]]>
</xsl:variable>

<xsl:variable name="systemLog_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <system_log id="http://hostname/api/inventory/systems/1/system_log">
        ...
      </system_log>

  POST:
    not supported
    
  PUT:
    not supported
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
