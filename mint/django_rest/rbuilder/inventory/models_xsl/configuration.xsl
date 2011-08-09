<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="configuration_info">
<xsl:copy-of select="$configuration_model" />
<xsl:copy-of select="$configuration_methods" />
</xsl:variable>

<xsl:variable name="configuration_model"><![CDATA[
Description:
  The configuration data for a system in inventory]]>
<xsl:copy-of select="$configuration_model_properties" />
</xsl:variable>

<xsl:variable name="configuration_model_properties"><![CDATA[]]>
</xsl:variable>

<xsl:variable name="configuration_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
