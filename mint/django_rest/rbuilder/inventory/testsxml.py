#!/usr/bin/python

inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <log href="http://testserver/api/inventory/log/"/>
  <managementNodes href="http://testserver/api/inventory/managementNodes/"/>
  <systems href="http://testserver/api/inventory/systems/"/>
</inventory>"""

management_nodes_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNodes>
  <managementNode id="http://testserver/api/inventory/managementNodes/1/">
    <local>True</local>
    <managementNodeId>1</managementNodeId>
    <systemSet/>
    <system href="http://testserver/api/inventory/systems/1/"/>
  </managementNode>
  <managementNode id="http://testserver/api/inventory/managementNodes/2/">
    <local>False</local>
    <managementNodeId>2</managementNodeId>
    <systemSet/>
    <system href="http://testserver/api/inventory/systems/2/"/>
  </managementNode>
</managementNodes>"""

management_node_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode id="http://testserver/api/inventory/managementNodes/1/">
  <local>True</local>
  <managementNodeId>1</managementNodeId>
  <systemSet/>
  <system href="http://testserver/api/inventory/systems/1/"/>
</managementNode>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <system>
      <networks>
        <network>
          <deviceName>eth0</deviceName>
          <ipAddress>1.1.1.1</ipAddress>
          <ipv6Address/>
          <netmask>255.255.255.0</netmask>
          <portType>lan</portType>
          <primary/>
          <publicDnsName>testnetwork.example.com</publicDnsName>
        </network>
      </networks>
      <description>testsystemdescription</description>
      <name>testsystemname</name>
  </system>
  <local>True</local>
</managementNode>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1/">
    <installedSoftware/>
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <deviceName>eth0</deviceName>
        <ipAddress>1.1.1.1</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>1</networkId>
        <portType>lan</portType>
        <primary/>
        <publicDnsName>testnetwork.example.com</publicDnsName>
        <system href="http://testserver/api/inventory/systems/1/"/>
      </network>
    </networks>
    <systemJobs/>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <systemId>1</systemId>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <available/>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <systemEvent href="http://testserver/api/inventory/systemEvents/1/"/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1/">
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <deviceName>eth0</deviceName>
        <ipAddress>1.1.1.1</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>1</networkId>
        <portType>lan</portType>
        <primary/>
        <publicDnsName>testnetwork.example.com</publicDnsName>
      </network>
    </networks>
    <systemJobs/>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <available/>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <systemEvent href="http://testserver/api/inventory/systemEvents/1/"/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
  <system id="http://testserver/api/inventory/systems/2/">
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
    <generatedUuid>testsystem2generateduuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <deviceName>eth0</deviceName>
        <ipAddress>2.2.2.2</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>2</networkId>
        <portType>lan</portType>
        <primary/>
        <publicDnsName>testnetwork2.example.com</publicDnsName>
      </network>
    </networks>
    <systemJobs/>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <available/>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <systemEvent href="http://testserver/api/inventory/systemEvents/2/"/>
    <name>testsystemname</name>
    <localUuid>testsystem2localuuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1/">
  <installedSoftware/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <deviceName>eth0</deviceName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <primary/>
      <publicDnsName>testnetwork.example.com</publicDnsName>
      <system href="http://testserver/api/inventory/systems/1/"/>
    </network>
  </networks>
  <systemJobs/>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>1</systemId>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemEvent href="http://testserver/api/inventory/systemEvents/1/"/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <deviceName>eth0</deviceName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <portType>lan</portType>
      <primary/>
      <publicDnsName>testnetwork.example.com</publicDnsName>
    </network>
  </networks>
  <systemJobs/>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <osType/>
</system>"""

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1/">
  <installedSoftware/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <deviceName>eth0</deviceName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <primary/>
      <publicDnsName>testnetwork.example.com</publicDnsName>
      <system href="http://testserver/api/inventory/systems/1/"/>
    </network>
  </networks>
  <systemJobs/>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>1</systemId>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemEvent href="http://testserver/api/inventory/systemEvents/1/"/>
  <target href="http://testserver/catalog/clouds/testtargettype/instances/testtargetname"/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvents>
    <systemEvent id="http://testserver/api/inventory/systemEvents/1/">
        <eventType href="http://testserver/api/inventory/systemEventTypes/3/"/>
        <system href="http://testserver/api/inventory/systems/1/"/>
        <timeCreated>%s</timeCreated>
        <priority>50</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>1</systemEventId>
    </systemEvent>
    <systemEvent id="http://testserver/api/inventory/systemEvents/2/">
        <eventType href="http://testserver/api/inventory/systemEventTypes/1/"/>
        <system href="http://testserver/api/inventory/systems/1/"/>
        <timeCreated>%s</timeCreated>
        <priority>100</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>2</systemEventId>
    </systemEvent>
</systemEvents>
"""

system_event_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvent id="http://testserver/api/inventory/systemEvents/1/">
    <eventType href="http://testserver/api/inventory/systemEventTypes/3/"/>
    <system href="http://testserver/api/inventory/systems/1/"/>
    <timeCreated>%s</timeCreated>
    <priority>50</priority>
    <timeEnabled>%s</timeEnabled>
    <systemEventId>1</systemEventId>
</systemEvent>
"""

system_log = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemLog id="http://testserver/api/inventory/systems/1/systemLog/">
  <systemLogEntries>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>1</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System added to inventory</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>2</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System activated via ractivate</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>3</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>4</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>5</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>6</systemLogEntryId>
    </systemLogEntry>
  </systemLogEntries>
  <systemLogId>1</systemLogId>
  <system href="http://testserver/api/inventory/systems/1/"/>
</systemLog>
"""

systems_log = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemsLog>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <systemLogEntryId>1</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <systemLogEntryId>2</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
    <systemLogEntryId>3</systemLogEntryId>
  </systemLogEntry>
</systemsLog>
"""

system_version_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1/">
  <installedSoftware>
    <trove>
      <availableUpdates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1272410162.98</ordering>
          <revision>1-3-1</revision>
          <versionId>2</versionId>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1272410162.98</ordering>
          <revision>1-4-1</revision>
          <versionId>3</versionId>
        </version>
      </availableUpdates>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>group-clover-appliance</name>
      <troveId>1</troveId>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1272410162.98</ordering>
        <revision>1-2-1</revision>
        <versionId>1</versionId>
      </version>
    </trove>
    <trove>
      <availableUpdates/>
      <flavor>desktop is: x86_64</flavor>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>emacs</name>
      <troveId>2</troveId>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1272410163.98</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <versionId>4</versionId>
      </version>
    </trove>
  </installedSoftware>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <deviceName>eth0</deviceName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <primary/>
      <publicDnsName>testnetwork.example.com</publicDnsName>
      <system href="http://testserver/api/inventory/systems/1/"/>
    </network>
  </networks>
  <systemJobs/>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>1</systemId>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemEvent href="http://testserver/api/inventory/systemEvents/1/"/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>
"""
