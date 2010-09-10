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
  List the entry points into the inventory API
  
Methods: 
  GET:
    Authentication: none
    Result:
      <inventory>
        <eventTypes href="https://hostname/api/inventory/eventTypes/"/>
        <log href="https://hostname/api/inventory/log/"/>
        <systemStates href="https://hostname/api/inventory/systemStates/"/>
        <systems href="https://hostname/api/inventory/systems/"/>
        <zones href="https://hostname/api/inventory/zones/"/>
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

<xsl:template match="/eventTypes">
<xsl:comment>
<![CDATA[
Description:
  List the types of events that can be performed on systems
  
Methods: 
  GET:
    Authentication: none
    Result:
      <eventTypes>
        <eventType id="http://hostname/api/inventory/eventTypes/1/">
          <name>system registration</name>
          <systemEvents/>
          <priority>110</priority>
          <jobSet/>
          <eventTypeId>1</eventTypeId>
          <description>on-demand registration event</description>
        </eventType>
        <eventType id="http://hostname/api/inventory/eventTypes/2/">
          <name>immediate system poll</name>
          <systemEvents/>
          <priority>105</priority>
          <jobSet/>
          <eventTypeId>2</eventTypeId>
          <description>on-demand polling event</description>
        </eventType>
        <eventType id="http://hostname/api/inventory/eventTypes/3/">
          <name>system poll</name>
          <systemEvents/>
          <priority>50</priority>
          <jobSet/>
          <eventTypeId>3</eventTypeId>
          <description>standard polling event</description>
        </eventType>
        <eventType id="http://hostname/api/inventory/eventTypes/4/">
          <name>system apply update</name>
          <systemEvents/>
          <priority>50</priority>
          <jobSet/>
          <eventTypeId>4</eventTypeId>
          <description>apply an update to a system</description>
        </eventType>
        <eventType id="http://hostname/api/inventory/eventTypes/5/">
          <name>immediate system apply update</name>
          <systemEvents/>
          <priority>105</priority>
          <jobSet/>
          <eventTypeId>5</eventTypeId>
          <description>on-demand apply an update to a system</description>
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
  List the the valid states systems can be in
  
Methods: 
  GET:
    Authentication: none
    Result:
      <systemStates> 
        <systemState id="http://hostname/api/inventory/systemStates/1/"> 
          <systemStateId>1</systemStateId> 
          <description>Unmanaged</description> 
          <name>unmanaged</name> 
          <createdDate>2010-09-10T14:54:01.949475+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/2/"> 
          <systemStateId>2</systemStateId> 
          <description>Polling</description> 
          <name>registered</name> 
          <createdDate>2010-09-10T14:54:01.951945+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/3/"> 
          <systemStateId>3</systemStateId> 
          <description>Online</description> 
          <name>responsive</name> 
          <createdDate>2010-09-10T14:54:01.954141+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/4/"> 
          <systemStateId>4</systemStateId> 
          <description>Not responding: unknown</description> 
          <name>non-responsive-unknown</name> 
          <createdDate>2010-09-10T14:54:01.956562+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/5/"> 
          <systemStateId>5</systemStateId> 
          <description>Not responding: network unreachable</description> 
          <name>non-responsive-net</name> 
          <createdDate>2010-09-10T14:54:01.958771+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/6/"> 
          <systemStateId>6</systemStateId> 
          <description>Not responding: host unreachable</description> 
          <name>non-responsive-host</name> 
          <createdDate>2010-09-10T14:54:01.961157+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/7/"> 
          <systemStateId>7</systemStateId> 
          <description>Not responding: shutdown</description> 
          <name>non-responsive-shutdown</name> 
          <createdDate>2010-09-10T14:54:01.963304+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/8/"> 
          <systemStateId>8</systemStateId> 
          <description>Not responding: suspended</description> 
          <name>non-responsive-suspended</name> 
          <createdDate>2010-09-10T14:54:01.966109+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/9/"> 
          <systemStateId>9</systemStateId> 
          <description>Stale</description> 
          <name>dead</name> 
          <createdDate>2010-09-10T14:54:01.968931+00:00</createdDate> 
        </systemState> 
        <systemState id="http://hostname/api/inventory/systemStates/10/"> 
          <systemStateId>10</systemStateId> 
          <description>Retired</description> 
          <name>mothballed</name> 
          <createdDate>2010-09-10T14:54:01.970909+00:00</createdDate> 
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
