<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
	<xsl:template match="/rbuilderStatus">
	<xsl:comment>
	Methods: GET

	Attributes:
	  The root level resource that provides links to all available resources
	exposed by this rBuilder. This resource is thus the key to discoverability
	of the rBuilder API.
	</xsl:comment>
	<xsl:copy-of select="/"/>    
	</xsl:template>

<xsl:template match="/reports">
<xsl:comment>
Methods: GET

Attributes:
  Basic information about the available reports
  Each report can be addressed separately by using the 'id' as its URL
</xsl:comment>
<xsl:copy-of select="/"/>    
</xsl:template>

<xsl:template match="/report">
<xsl:comment>
Methods: GET

Attributes:
  Name of the report
  Brief Description
  Linked Reference that describes how best to display the data
  Linked Reference to the report data
  Is this an admin report.  Non-admins will not be able to view this report.
  Is the report enabled and running
  URI name
  Creation Time
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/inventory">
<xsl:comment>
<![CDATA[
Description:
  A node listing the entry points into the inventory API

Properties:
  log - entry point into inventory logging
  systemStates - entry point into the inventory system states collection
  systems - entry point into the inventory systems collection
  zones - entry point into inventory management zones collection

Methods: 
  GET:
    Authentication: none
    Response Format:
      <inventory>
        <eventTypes href="http://hostname/api/inventory/eventTypes/"/>
        <log href="http://hostname/api/inventory/log/"/>
        <systemStates href="http://hostname/api/inventory/systemStates/"/>
        <systems href="http://hostname/api/inventory/systems/"/>
        <zones href="http://hostname/api/inventory/zones/"/>
      </inventory>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported
]]>
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/zones">
<xsl:comment>
<![CDATA[
Description:
  A collection of management zones available to inventory systems
  
Properties:
  zone - a management zone resource
    name - the zone name
    description - the zone description
    zoneId - the database id for the zone
    createdDate - the date the zone was created (UTC)
    managementNodes - a collection of management nodes in this zone
    systems - a collection of systems that are managed by this zone
  
Methods: 
  GET:
    Authentication: user
    Response Format:
      <zones>
        <zone id="http://hostname/api/inventory/zones/1/">
          ...
        </zone>
        <zone id="http://hostname/api/inventory/zones/2/">
          ...
        </zone>
      </zones>
      
  POST:
    Authentication: admin
    Required Fields:
      name
    Example:
      <zone>
        <name>East Datacenter</name>
        <description>Management zone for east datacenter</description>
      </zone>
    
  PUT:
    Authentication: admin
    
  DELETE:
    Authentication: admin
]]>
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/eventTypes">
<xsl:comment>
<![CDATA[
Description:
  A collection of event types applicable to systems in inventory
  
Properties:
  eventType - a system event type resource
    name - the event type name
    description - the event type description
    priority - the event type priority where > priority wins
    eventTypeId - the database id of the event type
    systemEvents - an entry point into a collection of all system events of this type
  
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
    not supported
]]>
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systemStates">
<xsl:comment>
<![CDATA[
Description:
  A collection of states applicable to systems in inventory
  
Properties:
  systemState - a system state resource
    name - the state name
    description - the state description
    systemStateId - the database id for the state
    createdDate - the date the state was created (UTC)
  
Methods: 
  GET:
    Authentication: none
    Response Format:
      <systemStates> 
        <systemState id="http://hostname/api/inventory/systemStates/1/">
          ...
        </systemState>
        <systemState id="http://hostname/api/inventory/systemStates/2/">
          ...
        </systemState>
      </systemStates>

  POST:
    not supported
    
  PUT:
    not supported
    
  DELETE:
    not supported
]]>
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systems">
<xsl:comment>
<![CDATA[
Description:
  A collection of systems in inventory
 
Properties:
    system - a system resource
    name - the system name
    description - the system description
    systemId - the database ID for the system
    createdDate - the date the system was added to inventory (UTC)
    registrationDate  - the date the system was registered in inventory (UTC)
    hostname - the system hostname
    osType - the system operating system type
    generatedUuid - a UUID that is randomly generated
    localUuid - a UUID created from the system hardware profile
    sslClientKey - an x509 private key of an authorized client that can use the system's CIM broker
    sslClientCertificate - an x509 certificate of an authorized client that can use the system's CIM broker
    sslServerCertificate - an x509 public certificate of the system's CIM broker
    currentState - the current state of the system
    networks - a collection of network resources exposed by the system
    installedSoftware - a collection of top-level items installed on the system
    managementNode - whether or not this system is a management node
    managingZone - a link to the management zone in which this system resides
    eventUuid - a UUID used to link system events with their returned responses
    launchingUser - the user that deployed the system (only applies if system is on a virtual target)
    launchDate - the date the system was deployed (only applies if system is on a virtual target)
    target - the virtual target the system was deployed to (only applies if system is on a virtual target)
    targetSystemId - the system ID as reported by its target (only applies if system is on a virtual target)
    targetSystemName - the system name as reported by its target (only applies if system is on a virtual target)
    targetSystemDescription - the system description as reported by its target (only applies if system is on a virtual target)
    targetSystemState - the system state as reported by its target (only applies if system is on a virtual target)
    
Identification of Duplicate Inventory Entries:
  Because systems can enter inventory in a number of different ways, a single system may initially appear in the inventory multiple times.
  The following information is used to identify these duplicate inventory entries:
    1)  localUuid and generatedUuid - Systems with identical local and generated UUIDs are guaranteed unique
    2)  target and targetSystemId - Virtual targets report a unique ID for each system and thus the combination
           of target and target system ID is guaranteed unique.
    3)  eventUuid - Event UUIDs are used to match system events with an incoming event response and can thus be used
           to lookup a specific system.
    
Methods: 
  GET:
    Authentication: user
    Response Format:
      <systems> 
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
    
  DELETE:
    Authentication: admin
]]>
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<!-- Catchall if the content does not match any of the above -->
<xsl:template match="/*">

    <xsl:copy-of select="/"/>

</xsl:template>
</xsl:stylesheet>
