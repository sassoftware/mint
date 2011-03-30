<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="credentials_info">
<xsl:copy-of select="$credentials_model" />
<xsl:copy-of select="$credentials_methods" />
</xsl:variable>

<xsl:variable name="credentials_model"><![CDATA[
Description:
  The credentials data for a system in inventory]]>
<xsl:copy-of select="$credentials_model_properties" />
</xsl:variable>

<xsl:variable name="credentials_model_properties"><![CDATA[]]>
</xsl:variable>

<xsl:variable name="credentials_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
