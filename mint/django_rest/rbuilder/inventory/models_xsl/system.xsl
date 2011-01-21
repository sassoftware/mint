<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="system_info">
<xsl:copy-of select="$system_model" />
<xsl:copy-of select="$system_methods" />
</xsl:variable>

<xsl:variable name="system_model"><![CDATA[
Description:
  The collection of all systems (all systems in /api/inventory_systems and /api/infrastructure systems combined)]]>
<xsl:copy-of select="$system_model_properties" />
<xsl:copy-of select="$system_model_dedup" />
</xsl:variable>

<xsl:variable name="system_model_properties"><![CDATA[
System Properties:]]>
<xsl:copy-of select="$system_model_properties_no_description" />
</xsl:variable>

<xsl:variable name="system_model_properties_no_description"><![CDATA[   agent_port - the port used by the system's management interface (CIM, WMI, etc.)
   appliance - the appliance of the system
   credentials - an entry point into the credentials data used for authentication with the system
   configuration - an entry point into the configuration data for this system
   configuration_descriptor - the descriptor of available fields to set system configuration parameters
   created_date - the date the system was added to inventory (UTC)
   current_state - the current state of the system
   description - the system description
   generated_uuid - a UUID that is randomly generated
   has_active_jobs - whether or not there are any jobs pending (queued or running) for this system
   has_running_jobs - whether or not there are any jobs running for this system
   hostname - the hostname reported by the system
   installed_software - an entry point into the collection of software installed on this system
   jobs - a collection of all jobs for this system
   launch_date - the date the system was deployed (only applies if system is on a virtual target)
   launching_user - the user that deployed the system (only applies if system is on a virtual target)
   local_uuid - a UUID created from the system hardware profile
   major_version - the appliance major version of the system
   management_interface - the management interface used to communicate with the system (CIM, WMI, etc.)
   managing_zone - a link to the management zone in which this system resides
   name - the name assigned when system was added to the inventory
   registration_date - the date the system was registered in inventory (UTC)
   ssl_client_certificate - an x509 certificate of an authorized client that can use the system's CIM broker
   ssl_client_key - an x509 private key of an authorized client that can use the system's CIM broker
   ssl_server_certificate - an x509 public certificate of the system's CIM broker
   stage - the appliance stage of the system
   system_id - the database ID for the system
   system_log - an entry point into the log data for this system
   system_type - the type of the system
   target - the virtual target the system was deployed to (only applies if system is on a virtual target)
   target_system_description - the system description as reported by its target (only applies if system is on a virtual target)
   target_system_id - the system ID as reported by its target (only applies if system is on a virtual target)
   target_system_name - the system name as reported by its target (only applies if system is on a virtual target)
   target_system_state - the system state as reported by its target (only applies if system is on a virtual target)]]>
</xsl:variable>

<xsl:variable name="system_model_dedup"><![CDATA[
Identification of Duplicate System Inventory Entries:
  Because systems can enter inventory in a number of different ways, a single system may initially appear in the inventory multiple times.
  The following information is used to identify these duplicate inventory entries:
    1)  local_uuid and generated_uuid - Systems with identical local and generated UUIDs are guaranteed unique.
    2)  target and target_system_id - Virtual targets report a unique ID for each system and thus the combination
           of target and target system ID is guaranteed unique.
    3)  event_uuid - Event UUIDs are used to match system events with an incoming event response and can thus be used
           to lookup a specific system.]]>
</xsl:variable>

<xsl:variable name="system_methods"><![CDATA[
Methods: 
  GET:
    Authentication: user
    Response Format:
       <system id="http://hostname/api/inventory/systems/1/">
         ...
       </system>

  POST:
    not supported
    
  PUT:
    Authentication: user
    
  DELETE:
    Authentication: admin]]>
</xsl:variable>

</xsl:stylesheet>
