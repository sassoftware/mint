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
    Format:
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
    createdDate - the date the zone was created in UTC
    managementNodes - an entry point into the management nodes collection for this zone
    systems - an entry point into the collection of systems managed by this zone
  
Methods: 
  GET:
    Authentication: user
    Format:
      <zones>
        <zone id="http://hostname/api/inventory/zones/1/">
          ...
        </zone>
        <zone id="http://hostname/api/inventory/zones/2/">
          ...
        </zone>
      </zones>
      
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
    Format:
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
    createdDate - the date the state was created in UTC
  
Methods: 
  GET:
    Authentication: none
    Format:
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
&lt;systems&gt;
    &lt;system&gt;
      &lt;generatedUuid&gt;ea664f09-d9b3-1e2b-ffe4-a5959e66be33&lt;/generatedUuid&gt;
      &lt;localUuid&gt;37b57b01-48d7-11cb-afdb-fedb0213827a   &lt;/localUuid&gt;
      &lt;registrationDate&gt;2010-07-15 15:52:28.927696&lt;/registrationDate&gt;
      &lt;sslClientCertificate&gt;
        ssl client certificate contents
      &lt;/sslClientCertificate&gt;
      &lt;sslClientKey&gt;
        ssl client key contents
      &lt;/sslClientKey&gt;
      &lt;sslServerCertificate&gt;
        ssl server certificate contents
      &lt;/sslServerCertificate&gt;
      &lt;ipAddress&gt;172.16.144.75&lt;/ipAddress&gt;
      &lt;available&gt;True&lt;/available&gt;
      &lt;log href="https://hostname/api/inventory/systems/UNIQUE_ID/log"/&gt;
    &lt;/system&gt;
&lt;/systems&gt;

POST - server registrations, structure should match above
PUT - not supported
DELETE - not supported
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<!-- Catchall if the content does not match any of the above -->
<xsl:template match="/*">

    <xsl:copy-of select="/"/>

</xsl:template>
</xsl:stylesheet>
