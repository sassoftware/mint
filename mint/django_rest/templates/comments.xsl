<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:include href="../rbuilder/inventory/models.xsl"/>

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
<xsl:copy-of select="$inventoryInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/zones">
<xsl:comment>
<xsl:copy-of select="$zonesInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/zone">
<xsl:comment>
<xsl:copy-of select="$zoneInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/eventTypes">
<xsl:comment>
<xsl:copy-of select="$eventTypesInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/eventType">
<xsl:comment>
<xsl:copy-of select="$eventTypeInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systemStates">
<xsl:comment>
<xsl:copy-of select="$systemStatesInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systemState">
<xsl:comment>
<xsl:copy-of select="$systemStateInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systems">
<xsl:comment>
<xsl:copy-of select="$systemsInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system">
<xsl:comment>
<xsl:copy-of select="$systemInfo" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<!-- Catchall if the content does not match any of the above -->
<xsl:template match="/*">

    <xsl:copy-of select="/"/>

</xsl:template>
</xsl:stylesheet>
