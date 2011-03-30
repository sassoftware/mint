<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemType_info">
<xsl:copy-of select="$systemType_model" />
<xsl:copy-of select="$systemType_methods" />
</xsl:variable>

<xsl:variable name="systemType_model"><![CDATA[
Description:
  A system type in inventory]]>
<xsl:copy-of select="$systemType_model_properties" />
</xsl:variable>

<xsl:variable name="systemType_model_properties"><![CDATA[   created_date - the date the system type was added to inventory (UTC)
   creation_descriptor - the descriptor of available fields to create systems of this type
   description - the description of the system type
   infrastructure - whether or not the system type is infrastructure
   name - the name of the system type
   system_type_id - the database ID for the system type]]>
</xsl:variable>

<xsl:variable name="systemType_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
