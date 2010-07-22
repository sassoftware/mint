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

	<xsl:template match="/report">
		
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
Methods: GET
&lt;inventory&gt;
  &lt;systems href="https://hostname/api/inventory/systems"/&gt;
  &lt;log href="https://hostname/api/inventory/log"/&gt;
&lt;/inventory&gt;

POST, PUT, and DELETE are not supported
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systems">
<xsl:comment>
Methods: 

GET - returns:
&lt;systems&gt;
    &lt;system&gt;
      &lt;generatedUuid&gt;ea664f09-d9b3-1e2b-ffe4-a5959e66be33&lt;/generatedUuid&gt;
      &lt;localUuid&gt;37b57b01-48d7-11cb-afdb-fedb0213827a   &lt;/localUuid&gt;
      &lt;activationDate&gt;2010-07-15 15:52:28.927696&lt;/activationDate&gt;
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

POST - server activations, structure should match above
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
