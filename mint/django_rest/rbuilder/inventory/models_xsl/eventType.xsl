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

<xsl:variable name="event_type_model_properties"><![CDATA[
EventType Properties:
  name - the event type name (read-only)
  description - the event type description
  priority - the event type priority where > priority wins
  event_type_id - the database id of the event type
  system_events - an entry point into a collection of all system events of this type]]>
</xsl:variable>

<xsl:variable name="event_type_methods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
       <event_type id="http://hostname/api/inventory/event_types/1/">
         ...
       </event_type>
      
  POST:
    not supported
    
  PUT:
    Authentication: admin
    Read-only fields:
        name
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
