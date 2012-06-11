<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventType.xsl"/>

<xsl:variable name="event_types_info">
<xsl:copy-of select="$event_types_model" />
<xsl:copy-of select="$event_types_methods" />
</xsl:variable>

<xsl:variable name="event_types_model"><![CDATA[
Description:
  A collection of event types applicable to systems in inventory
  
event_types Properties:
  event_type - a system event type resource]]>
<xsl:copy-of select="$event_type_model_properties" />
</xsl:variable>

<xsl:variable name="event_types_methods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <event_types>
        <event_type id="http://hostname/api/inventory/event_types/1/">
          ...
        </event_type>
        <event_type id="http://hostname/api/inventory/event_types/2/">
          ...
        </event_type>
      </event_types>
      
  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
