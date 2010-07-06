<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
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
</xsl:stylesheet>
