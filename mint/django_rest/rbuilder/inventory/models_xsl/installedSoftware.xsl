<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="installedSoftware_info">
<xsl:copy-of select="$installedSoftware_model" />
<xsl:copy-of select="$installedSoftware_methods" />
</xsl:variable>

<xsl:variable name="installedSoftware_model"><![CDATA[
Description:
  A collection of troves installed on a system]]>
<xsl:copy-of select="$installedSoftware_model_properties" />
</xsl:variable>

<xsl:variable name="installedSoftware_model_properties"><![CDATA[
InstalledSoftware Properties:
  trove - trove resource]]>
</xsl:variable>

<xsl:variable name="installedSoftware_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <installed_software id="http://hostname/api/inventory/sytems/1/installed_software">
         ...
       </installed_software>
      
  POST:
    not supported
    
  PUT:
    Authentication: user
    Notes:
        This will update the installed software on the system
    
  DELETE:
    not supported]]>
</xsl:variable>

</xsl:stylesheet>
