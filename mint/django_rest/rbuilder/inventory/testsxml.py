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
  <description>on-demand activation event</description><priority>110</priority>
  <jobSet/>
  <eventTypeId>1</eventTypeId>
  <name>system activation</name>
</eventType>"""

event_types_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventTypes>
  <eventType id="http://testserver/api/inventory/eventTypes/1/">
    <name>system activation</name>
    <systemEvents href="http://testserver/api/inventory/systemEventsByType/1/"/>
    <priority>110</priority>
    <jobSet/>
    <eventTypeId>1</eventTypeId>
    <description>on-demand activation event</description>
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
  <systemSet/>
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
    <activated>True</activated>
    <sslClientKey>test management node client key</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
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
        <system href="http://testserver/api/inventory/systems/1"/>
      </network>
    </networks>
    <systemJobs/>
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
    <sslClientCertificate>test management node client cert</sslClientCertificate>
    <installedSoftware/>
    <description>test management node desc</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <systemjobSet/>
    <target/>
    <zone href="http://testserver/api/inventory/zones/2/"/>
    <systemPtr href="http://testserver/api/inventory/systems/1"/>
    <localUuid>test management node luuid</localUuid>
    <currentState>activated</currentState>
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
  <activated>True</activated>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
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
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <systemJobs/>
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
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <installedSoftware/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemjobSet/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <available/>
  <activated>True</activated>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
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
  <systemJobs/>
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
  <currentState>activated</currentState>
  <osType/>
</managementNode>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <available>False</available>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <activated>True</activated>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName/>
      <dnsName/>
      <ipAddress/>
      <ipv6Address/>
      <netmask/>
      <networkId>1</networkId>
      <portType/>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <systemJobs/>
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
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <installedSoftware/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemjobSet/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1">
    <installedSoftware/>
    <activated/>
    <sslClientKey/>
    <osMajorVersion/>
    <activationDate/>
    <generatedUuid/>
    <managingNode/>
    <reservationId/>
    <networks/>
    <systemJobs/>
    <sslServerCertificate/>
    <systemId>1</systemId>
    <launchingUser/>
    <scheduledEventStartDate/>
    <launchDate/>
    <sslClientCertificate/>
    <available/>
    <description>Local rBuilder management node</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <osMinorVersion/>
    <isManagementNode>True</isManagementNode>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <target/>
    <name>Local Management Node</name>
    <localUuid/>
    <currentState/>
    <createdDate>2010-08-18T22:28:26+00:00</createdDate>
    <osType/>
  </system>
  <system id="http://testserver/api/inventory/systems/2">
    <installedSoftware/>
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <managingNode/>
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
    <systemJobs/>
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
    <isManagementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <target/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>
"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1">
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
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
    <isManagementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
  <system id="http://testserver/api/inventory/systems/2">
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate/>
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
    <isManagementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystem2localuuid</localUuid>
    <currentState>activated</currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  <installedSoftware/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingNode/>
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
  <systemJobs/>
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
  <isManagementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
  <target/>
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
  <currentState>activated</currentState>
  <osType/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <available/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <reservationId/>
  <networks>
    <network>
      <active/>
      <deviceName/>
      <dnsName/>
      <ipAddress/>
      <ipv6Address/>
      <netmask/>
      <networkId>1</networkId>
      <portType/>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <systemJobs/>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode/>
  <scheduledEventStartDate/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <installedSoftware/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <osMinorVersion/>
  <systemjobSet/>
  <name>testsystemname</name>
  <target/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_xml_dup = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <activated>False</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
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
<system id="http://testserver/api/inventory/systems/2">
  <installedSoftware/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingNode/>
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
  </systemJobs>
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
  <isManagementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
  <target href="http://testserver/catalog/clouds/testtargettype/instances/testtargetname"/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>
"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvents>
    <systemEvent id="http://testserver/api/inventory/systemEvents/1/">
        <eventType href="http://testserver/api/inventory/eventTypes/3/"/>
        <system href="http://testserver/api/inventory/systems/2"/>
        <timeCreated>%s</timeCreated>
        <priority>50</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>1</systemEventId>
    </systemEvent>
    <systemEvent id="http://testserver/api/inventory/systemEvents/2/">
        <eventType href="http://testserver/api/inventory/eventTypes/1/"/>
        <system href="http://testserver/api/inventory/systems/2"/>
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
    <eventType href="http://testserver/api/inventory/eventTypes/3/"/>
    <system href="http://testserver/api/inventory/systems/2"/>
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
<systemLog id="http://testserver/api/inventory/systems/2/systemLog/">
  <systemLogEntries>
    <systemLogEntry>
      <entry>System added to inventory</entry>
      <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
      <systemLogEntryId>1</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System activated via ractivate</entry>
      <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
      <systemLogEntryId>2</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
      <systemLogEntryId>3</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
      <systemLogEntryId>4</systemLogEntryId>
    </systemLogEntry>
    <systemLogEntry>
      <entry>System data fetched.</entry>
      <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
      <systemLogEntryId>5</systemLogEntryId>
    </systemLogEntry>
  </systemLogEntries>
  <systemLogId>1</systemLogId>
  <system href="http://testserver/api/inventory/systems/2"/>
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

installed_software_xml = """\
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
      <isTopLevel>True</isTopLevel>
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
      <isTopLevel>False</isTopLevel>
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
"""

system_version_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingNode/>
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
  </systemJobs>
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
  <isManagementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>%%s</createdDate>
  <osType/>
</system>
""" % installed_software_xml

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
</system>
""" % installed_software_post_xml

system_version_put_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingNode/>
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
  <systemJobs/>
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
  <isManagementNode/>
  <systemjobSet/>
  <target/>
  <name/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState>activated</currentState>
  <createdDate>2010-08-23T21:41:31.278455+00:00</createdDate>
  <osType/>
</system>
""" % installed_software_response_xml
