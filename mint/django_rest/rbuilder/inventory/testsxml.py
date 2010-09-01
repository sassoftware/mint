#!/usr/bin/python

inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <eventTypes href="http://testserver/api/inventory/eventTypes/"/>
  <log href="http://testserver/api/inventory/log/"/>
  <zones href="http://testserver/api/inventory/zones/"/>
  <systems href="http://testserver/api/inventory/systems/"/>
</inventory>"""

event_type_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventType id="http://testserver/api/inventory/eventTypes/1/">
  <systemEvents href="http://testserver/api/inventory/systemEventsByType/1/"/>
  <description>on-demand registration event</description><priority>110</priority>
  <jobSet/>
  <eventTypeId>1</eventTypeId>
  <name>system registration</name>
</eventType>"""

event_types_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventTypes>
  <eventType id="http://testserver/api/inventory/eventTypes/1/">
    <name>system registration</name>
    <systemEvents href="http://testserver/api/inventory/systemEventsByType/1/"/>
    <priority>110</priority>
    <jobSet/>
    <eventTypeId>1</eventTypeId>
    <description>on-demand registration event</description>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/2/">
    <name>immediate system poll</name>
    <systemEvents href="http://testserver/api/inventory/systemEventsByType/2/"/>
    <priority>105</priority>
    <jobSet/>
    <eventTypeId>2</eventTypeId>
    <description>on-demand polling event</description>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/3/">
    <name>system poll</name>
    <systemEvents href="http://testserver/api/inventory/systemEventsByType/3/"/>
    <priority>50</priority>
    <jobSet/>
    <eventTypeId>3</eventTypeId>
    <description>standard polling event</description>
  </eventType>
</eventTypes>"""

zones_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zones>
  <zone id="http://testserver/api/inventory/zones/1/">
    <systems/>
    <description>Some local zone</description>
    <createdDate>%s</createdDate>
    <name>Local Zone</name>
    <managementNodes/>
    <zoneId>1</zoneId>
  </zone>
</zones>
"""

zone_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/2/">
  <systems/>
  <description>Some local zone</description>
  <createdDate>%s</createdDate>
  <name>Local Zone</name>
  <managementNodes/>
  <zoneId>2</zoneId>
</zone>
"""

zone_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone>
  <description>Some local zone</description>
  <name>Local Zone</name>
</zone>
"""

zone_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/1/">
  <systems/>
  <description>Some local zone</description>
  <createdDate>%s</createdDate>
  <name>Local Zone</name>
  <managementNodes/>
  <zoneId>1</zoneId>
</zone>
"""

management_nodes_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNodes>
  <managementNode>
    <available/>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <registered>True</registered>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>test management node guuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <active/>
        <createdDate>%s</createdDate>
        <deviceName>eth0</deviceName>
        <dnsName>testnetwork.example.com</dnsName>
        <ipAddress>2.2.2.2</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>1</networkId>
        <portType>lan</portType>
        <required/>
        <system href="http://testserver/api/inventory/systems/1"/>
      </network>
    </networks>
    <nodeJid/>
    <sslServerCertificate>test management node server cert</sslServerCertificate>
    <managingZone/>
    <hostname/>
    <name>test management node</name>
    <systemId>1</systemId>
    <launchingUser/>
    <managementNode>True</managementNode>
    <scheduledEventStartDate/>
    <launchDate/>
    <local>True</local>
    <installedSoftware/>
    <description>test management node desc</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <target/>
    <zone href="http://testserver/api/inventory/zones/2/"/>
    <systemPtr href="http://testserver/api/inventory/systems/1"/>
    <localUuid>test management node luuid</localUuid>
    <currentState>registered</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </managementNode>
</managementNodes>
"""

management_node_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <available/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <createdDate>%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>2.2.2.2</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <nodeJid/>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>True</managementNode>
  <scheduledEventStartDate/>
  <launchDate/>
  <local>True</local>
  <installedSoftware/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <available/>
  <registered>True</registered>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>2.2.2.2</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required/>
    </network>
  </networks>
  <nodeJid>abcd</nodeJid>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>True</managementNode>
  <local>True</local>
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <description>test management node desc</description>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <localUuid>test management node luuid</localUuid>
  <currentState>registered</currentState>
  <osType/>
</managementNode>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <available>False</available>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active>False</active>
      <createdDate>%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>2.2.2.2</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required>False</required>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <nodeJid>abcd</nodeJid>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>True</managementNode>
  <scheduledEventStartDate/>
  <launchDate/>
  <local>True</local>
  <installedSoftware/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/2">
    <registered/>
    <registrationDate/>
    <available/>
    <createdDate>2010-08-18T22:28:26+00:00</createdDate>
    <currentState>unmanaged</currentState>
    <description>Local rPath Update Service</description>
    <generatedUuid/>
    <hostname/>
    <installedSoftware/>
    <launchDate/>
    <launchingUser/>
    <localUuid/>
    <managementNode>True</managementNode>
    <managingZone href="http://testserver/api/inventory/zones/1/"/>
    <name>rPath Update Service</name>
    <networks>
      <network>
        <active/>
        <createdDate>2010-08-18T22:28:26+00:00</createdDate>
        <deviceName/>
        <dnsName>127.0.0.1</dnsName>
        <ipAddress/>
        <ipv6Address/>
        <netmask/>
        <networkId>1</networkId>
        <portType/>
        <required/>
        <system href="http://testserver/api/inventory/systems/2"/>
      </network>
    </networks>
    <osMajorVersion/>
    <osMinorVersion/>
    <osType/>
    <reservationId/>
    <scheduledEventStartDate/>
    <sslServerCertificate/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <systemId>2</systemId>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <target/>
    <targetSystemId/>
  </system>
  <system id="http://testserver/api/inventory/systems/3">
    <registered>True</registered>
    <registrationDate/>
    <available/>
    <createdDate>%s</createdDate>
    <currentState>registered</currentState>
    <description>testsystemdescription</description>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <hostname/>
    <installedSoftware/>
    <launchDate/>
    <launchingUser/>
    <localUuid>testsystemlocaluuid</localUuid>
    <managementNode/>
    <managingZone/>
    <name>testsystemname</name>
    <networks>
      <network>
        <active/>
        <createdDate>%s</createdDate>
        <deviceName>eth0</deviceName>
        <dnsName>testnetwork.example.com</dnsName>
        <ipAddress>1.1.1.1</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>2</networkId>
        <portType>lan</portType>
        <required/>
        <system href="http://testserver/api/inventory/systems/3"/>
      </network>
    </networks>
    <osMajorVersion/>
    <osMinorVersion/>
    <osType/>
    <reservationId/>
    <scheduledEventStartDate/>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
    <systemId>3</systemId>
    <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
    <target/>
    <targetSystemId/>
  </system>
</systems>
"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1">
    <registered>True</registered>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <active/>
        <deviceName>eth0</deviceName>
        <dnsName>testnetwork.example.com</dnsName>
        <ipAddress>1.1.1.1</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>1</networkId>
        <portType>lan</portType>
        <required/>
      </network>
    </networks>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <available/>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <managementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState>registered</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
  <system id="http://testserver/api/inventory/systems/2">
    <registered>True</registered>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>testsystem2generateduuid</generatedUuid>
    <reservationId/>
    <networks>
      <network>
        <active/>
        <deviceName>eth0</deviceName>
        <dnsName>testnetwork2.example.com</dnsName>
        <ipAddress>2.2.2.2</ipAddress>
        <ipv6Address/>
        <netmask>255.255.255.0</netmask>
        <networkId>2</networkId>
        <portType>lan</portType>
        <required/>
      </network>
    </networks>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <available/>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <managementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystem2localuuid</localUuid>
    <currentState>registered</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <installedSoftware/>
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingZone/>
  <reservationId/>
  <hostname/>
  <networks>
    <network>
      <active/>
      <createdDate>%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>1</systemId>
  <launchingUser/>
  <scheduledEventStartDate/>
  <launchDate/>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <managementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <registered>True</registered>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <portType>lan</portType>
      <required/>
    </network>
  </networks>
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
  <currentState>registered</currentState>
  <osType/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <available>False</available>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active>False</active>
      <createdDate>%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required>False</required>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode/>
  <scheduledEventStartDate/>
  <launchDate/>
  <installedSoftware/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <target/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_xml_dup = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <registered>False</registered>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <portType>lan</portType>
      <required/>
    </network>
  </networks>
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
  <currentState>dead</currentState>
  <osType/>
</system>"""

system_post_xml_dup2 = system_post_xml_dup.replace(
    '<currentState>dead</currentState>', 
    '<currentState>mothballed</currentState>')

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <available/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <createdDate>%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode/>
  <scheduledEventStartDate/>
  <launchDate/>
  <installedSoftware/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <target href="http://testserver/catalog/clouds/testtargettype/instances/testtargetname"/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>
"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvents>
    <systemEvent id="http://testserver/api/inventory/systemEvents/1/">
        <eventData/>
        <eventType href="http://testserver/api/inventory/eventTypes/3/"/>
        <system href="http://testserver/api/inventory/systems/3"/>
        <timeCreated>%s</timeCreated>
        <priority>50</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>1</systemEventId>
    </systemEvent>
    <systemEvent id="http://testserver/api/inventory/systemEvents/2/">
        <eventData/>
        <eventType href="http://testserver/api/inventory/eventTypes/1/"/>
        <system href="http://testserver/api/inventory/systems/3"/>
        <timeCreated>%s</timeCreated>
        <priority>110</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>2</systemEventId>
    </systemEvent>
</systemEvents>
"""

system_event_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvent id="http://testserver/api/inventory/systemEvents/1/">
    <eventData/>
    <eventType href="http://testserver/api/inventory/eventTypes/3/"/>
    <system href="http://testserver/api/inventory/systems/3"/>
    <timeCreated>%s</timeCreated>
    <priority>50</priority>
    <timeEnabled>%s</timeEnabled>
    <systemEventId>1</systemEventId>
</systemEvent>
"""

system_event_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvent>
    <eventType href="http://testserver/api/inventory/eventTypes/3/"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</systemEvent>
"""

system_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemLog id="http://testserver/api/inventory/systems/1/systemLog/">
  <systemLogEntries>
    <systemLogEntry>
      <entry>System added to inventory</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>1</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System registered via rpath-tools</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>2</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>3</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
      <systemLogEntryId>4</systemLogEntryId>
    </systemLogEntry>
  </systemLogEntries>
  <systemLogId>1</systemLogId>
  <system href="http://testserver/api/inventory/systems/1"/>
</systemLog>
"""

systems_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemsLog>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
    <systemLogEntryId>1</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/4/systemLog/"/>
    <systemLogEntryId>2</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/5/systemLog/"/>
    <systemLogEntryId>3</systemLogEntryId>
  </systemLogEntry>
</systemsLog>
"""

get_installed_software_xml = """\
  <installedSoftware>
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%%3D/clover.eng.rpath.com%%40rpath%%3Aclover-1-devel/1-2-1%%5B%%7E%%21dom0%%2C%%7E%%21domU%%2Cvmware%%2C%%7E%%21xen%%20is%%3A%%20x86%%28i486%%2Ci586%%2Ci686%%2Csse%%2Csse2%%29%%5D">
      <availableUpdates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567891.13</ordering>
          <revision>1-3-1</revision>
          <versionId>2</versionId>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567892.14</ordering>
          <revision>1-4-1</revision>
          <versionId>3</versionId>
        </version>
      </availableUpdates>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
      <isTopLevel>True</isTopLevel>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>group-clover-appliance</name>
      <troveId>1</troveId>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <versionId>1</versionId>
      </version>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%%3D/contrib.rpath.org%%40rpl%%3A2/23.0.60cvs20080523-1-0.1%%5Bdesktop%%20is%%3A%%20x86_64%%5D">
      <availableUpdates/>
      <flavor>desktop is: x86_64</flavor>
      <isTopLevel>False</isTopLevel>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>emacs</name>
      <troveId>2</troveId>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <versionId>4</versionId>
      </version>
    </trove>
  </installedSoftware>
"""

installed_software_xml = """\
  <installedSoftware>
    <trove>
      <availableUpdates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.13</ordering>
          <revision>1-3-1</revision>
          <versionId>2</versionId>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.14</ordering>
          <revision>1-4-1</revision>
          <versionId>3</versionId>
        </version>
      </availableUpdates>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
      <isTopLevel>True</isTopLevel>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>group-clover-appliance</name>
      <troveId>1</troveId>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <versionId>1</versionId>
      </version>
    </trove>
    <trove>
      <availableUpdates/>
      <flavor>desktop is: x86_64</flavor>
      <isTopLevel>False</isTopLevel>
      <lastAvailableUpdateRefresh>%s</lastAvailableUpdateRefresh>
      <name>emacs</name>
      <troveId>2</troveId>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <versionId>4</versionId>
      </version>
    </trove>
  </installedSoftware>
"""

system_version_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/3">
  %s
  <registered>True</registered>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingZone/>
  <reservationId/>
  <hostname/>
  <networks>
    <network>
      <active/>
      <createdDate>%%s</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>2</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/3"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>3</systemId>
  <launchingUser/>
  <scheduledEventStartDate/>
  <launchDate/>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <managementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>%%s</createdDate>
  <osType/>
</system>
""" % get_installed_software_xml

installed_software_post_xml = """\
  <installedSoftware>
    <trove>
      <name>group-chater-appliance</name>
      <version>
        <full>/chater.eng.rpath.com@rpath:chater-1-devel/1-2-1</full>
        <ordering>1234567890.12</ordering>
        <flavor>is: x86</flavor>
      </version>
      <flavor>is: x86</flavor>
    </trove>
    <trove>
      <name>vim</name>
      <version>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <ordering>1272410163.98</ordering>
        <flavor>desktop is: x86_64</flavor>
      </version>
      <flavor>desktop is: x86_64</flavor>
    </trove>
    <trove>
      <name>info-sfcb</name>
      <version>
        <full>/contrib.rpath.org@rpl:2/1-1-1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <revision>1-1-1</revision>
        <ordering>1263856871.03</ordering>
        <flavor/>
      </version>
      <flavor/>
    </trove>
  </installedSoftware>
"""

installed_software_response_xml = """
  <installedSoftware>
    <trove>
      <availableUpdates/>
      <flavor>is: x86</flavor>
      <isTopLevel>True</isTopLevel>
      <lastAvailableUpdateRefresh>XXX</lastAvailableUpdateRefresh>
      <name>group-chater-appliance</name>
      <troveId>3</troveId>
      <version>
        <flavor>is: x86</flavor>
        <full>/chater.eng.rpath.com@rpath:chater-1-devel/1-2-1</full>
        <label>chater.eng.rpath.com@rpath:chater-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>1-2-1</revision>
        <versionId>5</versionId>
      </version>
    </trove>
    <trove>
      <availableUpdates/>
      <flavor>desktop is: x86_64</flavor>
      <isTopLevel>False</isTopLevel>
      <lastAvailableUpdateRefresh>XXX</lastAvailableUpdateRefresh>
      <name>vim</name>
      <troveId>4</troveId>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1272410163.98</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <versionId>6</versionId>
      </version>
    </trove>
  </installedSoftware>
"""

system_version_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <localUuid>testsystemlocaluuid</localUuid>
  <name>somesystem</name>
</system>
""" % installed_software_post_xml

system_version_put_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
  <registered>True</registered>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingZone/>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>1</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/2"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>2</systemId>
  <launchingUser/>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <available/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <managementNode/>
  <target/>
  <name/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>2010-08-23T21:41:31.278455+00:00</createdDate>
  <osType/>
</system>
""" % installed_software_response_xml

system_available_updates_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/3">
  <installedSoftware>
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%3D/clover.eng.rpath.com%40rpath%3Aclover-1-devel/1-2-1%5B%7E%21dom0%2C%7E%21domU%2Cvmware%2C%7E%21xen%20is%3A%20x86%28i486%2Ci586%2Ci686%2Csse%2Csse2%29%5D">
      <name>group-clover-appliance</name>
      <troveId>1</troveId>
      <availableUpdates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567891.13</ordering>
          <revision>1-3-1</revision>
          <versionId>2</versionId>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567892.14</ordering>
          <revision>1-4-1</revision>
          <versionId>3</versionId>
        </version>
      </availableUpdates>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <versionId>1</versionId>
      </version>
      <lastAvailableUpdateRefresh>2010-08-27T12:21:59.802463+00:00</lastAvailableUpdateRefresh>
      <isTopLevel>True</isTopLevel>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>emacs</name>
      <troveId>2</troveId>
      <availableUpdates/>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <versionId>4</versionId>
      </version>
      <lastAvailableUpdateRefresh>2010-08-27T12:21:59.815100+00:00</lastAvailableUpdateRefresh>
      <isTopLevel>False</isTopLevel>
      <flavor>desktop is: x86_64</flavor>
    </trove>
  </installedSoftware>
  <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
  <osMajorVersion/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <createdDate>2010-08-27T12:21:59.801387+00:00</createdDate>
      <deviceName>eth0</deviceName>
      <dnsName>testnetwork.example.com</dnsName>
      <ipAddress>1.1.1.1</ipAddress>
      <ipv6Address/>
      <netmask>255.255.255.0</netmask>
      <networkId>2</networkId>
      <portType>lan</portType>
      <required/>
      <system href="http://testserver/api/inventory/systems/3"/>
    </network>
  </networks>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>3</systemId>
  <launchingUser/>
  <managementNode/>
  <scheduledEventStartDate/>
  <launchDate/>
  <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
  <available/>
  <registrationDate/>
  <description>testsystemdescription</description>
  <registered>True</registered>
  <targetSystemId/>
  <osMinorVersion/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>registered</currentState>
  <createdDate>2010-08-27T12:21:59.800269+00:00</createdDate>
  <osType/>
</system>
"""
