<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="network_info">
<xsl:copy-of select="$network_model" />
<xsl:copy-of select="$network_methods" />
</xsl:variable>

<xsl:variable name="network_model"><![CDATA[
Description:
  A network in inventory]]>
<xsl:copy-of select="$network_model_properties" />
</xsl:variable>

<xsl:variable name="network_model_properties"><![CDATA[   active - whether or not this is the active network device on the system
   created_date - the date the network was created (UTC)
   device_name - the network device name
   dns_name - the network DNS name
   ip_address - the network IP address
   ipv6_address - the network IPv6 address
   netmask - the network netmask
   network_id - the database ID for the network
   port_type - the network port type
   required - whether or not a user has required that this network device be the ones used to manage the system
   system - documentation missing]]>
</xsl:variable>

<xsl:variable name="network_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
