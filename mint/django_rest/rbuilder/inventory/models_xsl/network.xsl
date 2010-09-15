<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="networkInfo">
<xsl:copy-of select="$networkModel" />
<xsl:copy-of select="$networkMethods" />
</xsl:variable>

<xsl:variable name="networkModel"><![CDATA[
Description:
  A network in inventory]]>
<xsl:copy-of select="$networkModelProperties" />
</xsl:variable>

<xsl:variable name="networkModelProperties"><![CDATA[
Network Properties:
  deviceName - the network device name
  networkId - the database ID for the network
  createdDate - the date the network was created (UTC)
  ip_address - the network IP address
  ipv6_address - the network IPv6 address
  dns_name - the network DNS name
  netmask - the network netmask
  port_type - the network port type
  active - whether or not this is the active network device on the system
  required - whether or not a user has required that this network device be the ones used to manage the system]]>
</xsl:variable>

<xsl:variable name="networkMethods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <network id="http://hostname/api/inventory/networks/1/">
         ...
       </network>

  POST:
    not supported
    
  PUT:
    Authentication: admin
    
  DELETE:
    Authentication: admin]]>
</xsl:variable>

</xsl:stylesheet>