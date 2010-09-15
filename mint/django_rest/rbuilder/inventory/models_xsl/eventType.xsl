<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="eventTypeInfo">
<xsl:copy-of select="$eventTypeModel" />
<xsl:copy-of select="$eventTypeMethods" />
</xsl:variable>

<xsl:variable name="eventTypeModel"><![CDATA[
Description:
  A system event type]]>
<xsl:copy-of select="$eventTypeModelProperties" />
</xsl:variable>

<xsl:variable name="eventTypeModelProperties"><![CDATA[
EventType Properties:
  name - the event type name
  description - the event type description
  priority - the event type priority where > priority wins
  eventTypeId - the database id of the event type
  systemEvents - an entry point into a collection of all system events of this type]]>
</xsl:variable>

<xsl:variable name="eventTypeMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
       <eventType id="http://hostname/api/inventory/eventTypes/1/">
         ...
       </eventType>
      
  POST:
    not supported
    
  PUT:
    Authentication: admin
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>