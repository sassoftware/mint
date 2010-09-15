<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:variable name="systemInfo">
<xsl:copy-of select="$systemModel" />
<xsl:copy-of select="$systemMethods" />
</xsl:variable>

<xsl:variable name="systemModel"><![CDATA[
Description:
  A system in inventory]]>
<xsl:copy-of select="$systemModelProperties" />
<xsl:copy-of select="$systemModelDedup" />
</xsl:variable>

<xsl:variable name="systemModelProperties"><![CDATA[
System Properties:
    name - the system name
    description - the system description
    systemId - the database ID for the system
    createdDate - the date the system was added to inventory (UTC)
    registrationDate  - the date the system was registered in inventory (UTC)
    hostname - the system hostname
    osType - the system operating system type
    generatedUuid - a UUID that is randomly generated
    localUuid - a UUID created from the system hardware profile
    sslClientKey - an x509 private key of an authorized client that can use the system's CIM broker
    sslClientCertificate - an x509 certificate of an authorized client that can use the system's CIM broker
    sslServerCertificate - an x509 public certificate of the system's CIM broker
    currentState - the current state of the system
    networks - a collection of network resources exposed by the system
    installedSoftware - a collection of top-level items installed on the system
    managementNode - whether or not this system is a management node
    managingZone - a link to the management zone in which this system resides
    eventUuid - a UUID used to link system events with their returned responses
    launchingUser - the user that deployed the system (only applies if system is on a virtual target)
    launchDate - the date the system was deployed (only applies if system is on a virtual target)
    target - the virtual target the system was deployed to (only applies if system is on a virtual target)
    targetSystemId - the system ID as reported by its target (only applies if system is on a virtual target)
    targetSystemName - the system name as reported by its target (only applies if system is on a virtual target)
    targetSystemDescription - the system description as reported by its target (only applies if system is on a virtual target)
    targetSystemState - the system state as reported by its target (only applies if system is on a virtual target)]]>
</xsl:variable>

<xsl:variable name="systemModelDedup"><![CDATA[
Identification of Duplicate System Inventory Entries:
  Because systems can enter inventory in a number of different ways, a single system may initially appear in the inventory multiple times.
  The following information is used to identify these duplicate inventory entries:
    1)  localUuid and generatedUuid - Systems with identical local and generated UUIDs are guaranteed unique
    2)  target and targetSystemId - Virtual targets report a unique ID for each system and thus the combination
           of target and target system ID is guaranteed unique.
    3)  eventUuid - Event UUIDs are used to match system events with an incoming event response and can thus be used
           to lookup a specific system.]]>
</xsl:variable>

<xsl:variable name="systemMethods"><![CDATA[
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
    Authentication: none
    
  DELETE:
    Authentication: admin]]>
</xsl:variable>

</xsl:stylesheet>