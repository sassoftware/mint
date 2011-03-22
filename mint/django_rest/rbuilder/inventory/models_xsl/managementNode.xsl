<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:import href="systems.xsl"/>

<xsl:variable name="management_node_info">
<xsl:copy-of select="$management_node_model" />
<xsl:copy-of select="$management_node_methods" />
</xsl:variable>

<xsl:variable name="management_node_model"><![CDATA[
Description:
  A management node in inventory.]]>
<xsl:copy-of select="$management_node_model_properties" />
</xsl:variable>

<xsl:variable name="management_node_model_properties"><![CDATA[   agent_port - the port used by the system's CIM broker
   appliance - the appliance of the system
   created_date - the date the system was added to inventory (UTC)
   current_state - the current state of the system
   description - the system description
   generated_uuid - a UUID that is randomly generated
   hostname - the system hostname
   launch_date - the date the system was deployed (only applies if system is on a virtual target)
   launching_user - the user that deployed the system (only applies if system is on a virtual target)
   local - whether or not this management node is local to the rBuilder
   local_uuid - a UUID created from the system hardware profile
   major_version - the appliance major version of the system
   management_interface - the management interface used to communicate with the system
   managing_zone - a link to the management zone in which this system resides
   name - the system name
   node_jid - the Jabber ID the management node is using
   registration_date - the date the system was registered in inventory (UTC)
   ssl_client_certificate - an x509 certificate of an authorized client that can use the system's CIM broker
   ssl_client_key - an x509 private key of an authorized client that can use the system's CIM broker
   ssl_server_certificate - an x509 public certificate of the system's CIM broker
   stage - the appliance stage of the system
   system_id - the database ID for the system
   system_type - the type of the system
   target - the virtual target the system was deployed to (only applies if system is on a virtual target)
   target_system_description - the system description as reported by its target (only applies if system is on a virtual target)
   target_system_id - the system ID as reported by its target (only applies if system is on a virtual target)
   target_system_name - the system name as reported by its target (only applies if system is on a virtual target)
   target_system_state - the system state as reported by its target (only applies if system is on a virtual target)
   zone - the zone the management node lives in]]>
<xsl:copy-of select="$system_model_properties_no_description" /><![CDATA[   local - whether or not this management node is local to the rBuilder
   system_ptr - a link to the management node's underlying system
   zone - the zone the management node lives in
   node_jid - the Jabber ID the management node is using]]>
</xsl:variable>

<xsl:variable name="management_node_methods"><![CDATA[@@METHODS@@]]>
</xsl:variable>

</xsl:stylesheet>
