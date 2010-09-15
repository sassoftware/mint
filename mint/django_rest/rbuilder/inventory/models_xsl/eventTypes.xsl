<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventType.xsl"/>

<xsl:variable name="eventTypesInfo">
<xsl:copy-of select="$eventTypesModel" />
<xsl:copy-of select="$eventTypesMethods" />
</xsl:variable>

<xsl:variable name="eventTypesModel"><![CDATA[
Description:
  A collection of event types applicable to systems in inventory
  
EventTypes Properties:
  eventType - a system event type resource]]>
<xsl:copy-of select="$eventTypeModelProperties" />
</xsl:variable>

<xsl:variable name="eventTypesMethods"><![CDATA[
Methods: 
  GET:
    Authentication: none
    Response Format:
      <eventTypes>
        <eventType id="http://hostname/api/inventory/eventTypes/1/">
          ...
        </eventType>
        <eventType id="http://hostname/api/inventory/eventTypes/2/">
          ...
        </eventType>
      </eventTypes>
      
  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>