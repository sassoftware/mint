<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="system_state_info">
<xsl:copy-of select="$system_state_model" />
<xsl:copy-of select="$system_state_methods" />
</xsl:variable>

<xsl:variable name="system_state_model"><![CDATA[
Description:
  A system state resource]]>
<xsl:copy-of select="$system_state_model_properties" />
</xsl:variable>

<xsl:variable name="system_state_model_properties"><![CDATA[   created_date - the date the state was created (UTC)
   description - the state description
   name - the state name
   system_state_id - the database id for the state]]>
</xsl:variable>

<xsl:variable name="system_state_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
