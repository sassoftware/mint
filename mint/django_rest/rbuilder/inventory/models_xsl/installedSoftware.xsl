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
  trove - trove resource
  
Trove Properties:
  name - the name of the trove
  trove_id - the database ID for the trove
  is_top_level - whether or not the trove is a top-level group
  is_top_level_item - whether or not the trove is a top-level item (group or package)
  available_updates - a collection of trove versions representing updates to the trove (see below for more information)
  last_available_update_refresh - the last time the collection of available updates was refreshed
  flavor - the flavor of the trove
  
Available Updates Properties:
  version - a trove version resource (see below for more information)
  
Trove Version Properties:
  version_id - the database ID for the trove version
  flavor - the flavor of the trove version
  full - the full trovespec of the trove version
  label - the label of the trove version
  ordering - the ordering timestamp of the trove version
  revision - the version number of the trove version]]>
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
