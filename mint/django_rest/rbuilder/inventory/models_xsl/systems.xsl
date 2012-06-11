<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="system.xsl"/>

<xsl:variable name="systems_info">
<xsl:copy-of select="$systems_model" />
<xsl:copy-of select="$systems_methods" />
</xsl:variable>

<xsl:variable name="systems_model"><![CDATA[
Description:
  A collection of systems in inventory
  
Systems Properties:
  event_types - an entry point into system inventory event types
  system - a system resource]]>
<xsl:copy-of select="$event_types_href_model" />
<xsl:copy-of select="$system_model_properties" />
<xsl:copy-of select="$system_model_dedup" />
</xsl:variable>

<xsl:variable name="systems_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <systems>
        <event_types href="http://hostname/api/inventory/event_types/"/>
        <system id="http://hostname/api/inventory/systems/1/">
          ...
        </system>
        <system id="http://hostname/api/inventory/systems/2/">
          ...
        </system>
      </systems>

  POST:
    Authentication: none
    Required Fields:
      Technically only the name field is required.  This could result in duplicate entries in the inventory. 
      The recommended way is to include network information for the system so it can be contacted to initiate the registration process.
    Example:
      <system>
        <name>Billing System Application Server</name>
        <description>The app server for the HR billing system</description>
        <networks>
          <network>
            <dns_name>192.168.1.192</dns_name>
          </network>
        </networks>
      </system>
    
  PUT:
    Authentication: none
    Example:
      <systems>
        <system>
          <name>Billing System Application Server</name>
          <description>The app server for the HR billing system</description>
          <networks>
            <network>
              <dns_name>192.168.1.192</dns_name>
            </network>
          </networks>
        </system>
        <system>
          <name>Billing System File Server</name>
          <description>The file server for the HR billing system</description>
          <networks>
            <network>
              <dns_name>192.168.1.193</dns_name>
            </network>
          </networks>
        </system>
      <systems>
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
