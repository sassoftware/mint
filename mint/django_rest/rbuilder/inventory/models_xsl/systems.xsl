<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="eventTypesHref.xsl"/>
<xsl:import href="system.xsl"/>

<xsl:variable name="systemsInfo">
<xsl:copy-of select="$systemsModel" />
<xsl:copy-of select="$systemsMethods" />
</xsl:variable>

<xsl:variable name="systemsModel"><![CDATA[
Description:
  A collection of systems in inventory
  
Systems Properties:
    eventTypes - an entry point into system inventory event types
    system - a system resource]]>
<xsl:copy-of select="$eventTypesHrefModel" />
<xsl:copy-of select="$systemModelProperties" />
<xsl:copy-of select="$systemModelDedup" />
</xsl:variable>

<xsl:variable name="systemsMethods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
      <systems>
        <eventTypes href="http://hostname/api/inventory/eventTypes/"/>
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
      Technically only the name field is required.  This could result in duplicate entries in the inventory though. 
      The recommended way is to include network information for the system so it can be contacted to initiate the registration process.
    Example:
      <system>
        <name>Billing System Application Server</name>
        <descriptionThe app server for the HR billing system</description>
        <networks>
          <network>
            <dnsName>192.168.1.192</dnsName>
          </network>
        </networks>
      </system>
    
  PUT:
    Authentication: none
    Example:
      <systems>
        <system>
          <name>Billing System Application Server</name>
          <descriptionThe app server for the HR billing system</description>
          <networks>
            <network>
              <dnsName>192.168.1.192</dnsName>
            </network>
          </networks>
        </system>
        <system>
          <name>Billing System File Server</name>
          <descriptionThe file server for the HR billing system</description>
          <networks>
            <network>
              <dnsName>192.168.1.193</dnsName>
            </network>
          </networks>
        </system>
      <systems>
      
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>