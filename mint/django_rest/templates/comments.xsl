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
<xsl:copy-of select="$inventory_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/zones">
<xsl:comment>
<xsl:copy-of select="$zones_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/zone">
<xsl:comment>
<xsl:copy-of select="$zone_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/management_nodes">
<xsl:comment>
<xsl:copy-of select="$management_nodes_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/management_node">
<xsl:comment>
<xsl:copy-of select="$management_node_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/event_types">
<xsl:comment>
<xsl:copy-of select="$event_types_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/event_type">
<xsl:comment>
<xsl:copy-of select="$event_type_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system_states">
<xsl:comment>
<xsl:copy-of select="$system_states_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system_state">
<xsl:comment>
<xsl:copy-of select="$system_state_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/networks">
<xsl:comment>
<xsl:copy-of select="$networks_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/network">
<xsl:comment>
<xsl:copy-of select="$network_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/job_states">
<xsl:comment>
<xsl:copy-of select="$jobStates_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/job_state">
<xsl:comment>
<xsl:copy-of select="$jobState_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system_types">
<xsl:comment>
<xsl:copy-of select="$systemTypes_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system_type">
<xsl:comment>
<xsl:copy-of select="$systemType_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/management_interfaces">
<xsl:comment>
<xsl:copy-of select="$managementInterfaces_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/management_interface">
<xsl:comment>
<xsl:copy-of select="$managementInterface_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/systems">
<xsl:comment>
<xsl:copy-of select="$systems_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system">
<xsl:comment>
<xsl:copy-of select="$system_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/credentials">
<xsl:comment>
<xsl:copy-of select="$credentials_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/configuration">
<xsl:comment>
<xsl:copy-of select="$configuration_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/system_log">
<xsl:comment>
<xsl:copy-of select="$systemLog_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/jobs">
<xsl:comment>
<xsl:copy-of select="$jobs_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/job">
<xsl:comment>
<xsl:copy-of select="$job_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<xsl:template match="/installed_software">
<xsl:comment>
<xsl:copy-of select="$installedSoftware_info" />
</xsl:comment>
<xsl:copy-of select="/"/>
</xsl:template>

<!-- Catchall if the content does not match any of the above -->
<xsl:template match="/*">

    <xsl:copy-of select="/"/>

</xsl:template>
</xsl:stylesheet>
