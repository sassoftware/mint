<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="event_type_info">
<xsl:copy-of select="$event_type_model" />
<xsl:copy-of select="$event_type_methods" />
</xsl:variable>

<xsl:variable name="event_type_model"><![CDATA[
Description:
  A system event type]]>
<xsl:copy-of select="$event_type_model_properties" />
</xsl:variable>

<xsl:variable name="event_type_model_properties"><![CDATA[   description - the event type description
   event_type_id - the database id of the event type
   name - the event type name (read-only)
   priority - the event type priority where > priority wins]]>
</xsl:variable>

<xsl:variable name="event_type_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
