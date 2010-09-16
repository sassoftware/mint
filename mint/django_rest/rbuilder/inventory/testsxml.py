#!/usr/bin/python

inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <eventTypes href="http://testserver/api/inventory/eventTypes/"/>
  <jobStates href="http://testserver/api/inventory/jobStates/"/>
  <log href="http://testserver/api/inventory/log/"/>
  <zones href="http://testserver/api/inventory/zones/"/>
  <managementNodes href="http://testserver/api/inventory/managementNodes/"/>
  <systems href="http://testserver/api/inventory/systems/"/>
  <systemStates href="http://testserver/api/inventory/systemStates/"/>
  <networks href="http://testserver/api/inventory/networks/"/>
</inventory>"""

event_type_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventType id="http://testserver/api/inventory/eventTypes/1/">
  <description>on-demand registration event</description>
  <priority>110</priority>
  <jobSet/>
  <eventTypeId>1</eventTypeId>
  <name>system registration</name>
  <systemEvents/>
</eventType>"""

event_types_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventTypes>
  <eventType id="http://testserver/api/inventory/eventTypes/1/">
    <name>system registration</name>
    <priority>110</priority>
    <jobSet/>
    <eventTypeId>1</eventTypeId>
    <description>on-demand registration event</description>
    <systemEvents/>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/2/">
    <name>immediate system poll</name>
    <priority>105</priority>
    <jobSet/>
    <eventTypeId>2</eventTypeId>
    <description>on-demand polling event</description>
    <systemEvents/>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/3/">
    <name>system poll</name>
    <priority>50</priority>
    <jobSet/>
    <eventTypeId>3</eventTypeId>
    <description>standard polling event</description>
    <systemEvents/>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/4/">
    <description>apply an update to a system</description>
    <eventTypeId>4</eventTypeId>
    <jobSet/>
    <name>system apply update</name>
    <priority>50</priority>
    <systemEvents/>
  </eventType>
  <eventType id="http://testserver/api/inventory/eventTypes/5/">
    <description>on-demand apply an update to a system</description>
    <eventTypeId>5</eventTypeId>
    <jobSet/>
    <name>immediate system apply update</name>
    <priority>105</priority>
    <systemEvents/>
  </eventType>
</eventTypes>"""

event_type_put_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<eventType id="http://testserver/api/inventory/eventTypes/1/">
  <description>on-demand registration event</description>
  <priority>1</priority>
  <jobSet/>
  <eventTypeId>1</eventTypeId>
  <name>system registration</name>
  <systemEvents/>
</eventType>"""

zones_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zones>
  <zone id="http://testserver/api/inventory/zones/1/">
    <description>Some local zone</description>
    <createdDate>%s</createdDate>
    <name>Local Zone</name>
    <systems>
      <system id="http://testserver/api/inventory/systems/1">
        <agentPort/>
        <createdDate>2010-09-14T14:58:55.554533+00:00</createdDate>
        <currentState id="http://testserver/api/inventory/systemStates/1/">
          <createdDate>2010-09-14T14:58:40.939184+00:00</createdDate>
          <description>Unmanaged</description>
          <name>unmanaged</name>
          <systemStateId>1</systemStateId>
        </currentState>
        <description/>
        <generatedUuid/>
        <hostname/>
        <installedSoftware/>
        <jobs/>
        <launchDate/>
        <launchingUser/>
        <localUuid/>
        <managementNode/>
        <managingZone href="http://testserver/api/inventory/zones/1/"/>
        <name>foo</name>
        <networks/>
        <osMajorVersion/>
        <osMinorVersion/>
        <osType/>
        <registrationDate/>
        <sslClientCertificate/>
        <sslServerCertificate/>
        <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
        <systemId>1</systemId>
        <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
        <target/>
        <targetSystemDescription/>
        <targetSystemId/>
        <targetSystemName/>
        <targetSystemState/>
      </system>
    </systems>
    <managementNodes/>
    <zoneId>1</zoneId>
  </zone>
</zones>
"""

zone_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/1/">
  <description>Some local zone</description>
  <createdDate>%s</createdDate>
  <name>Local Zone</name>
  <systems/>
  <managementNodes/>
  <zoneId>1</zoneId>
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
  <description>Some local zone</description>
  <createdDate>%s</createdDate>
  <name>Local Zone</name>
  <managementNodes/>
  <zoneId>1</zoneId>
  <systems/>
</zone>
"""

zone_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/1/">
  <description>zoneputdesc</description>
  <name>zoneputname</name>
</zone>
"""

networks_xml = """\
<?xml version="1.0"?>
<networks>
  <systems href="http://testserver/api/inventory/systems/"/>
  <network id="http://testserver/api/inventory/networks/1/">
    <active/>
    <createdDate>2010-09-15T21:41:40.142078+00:00</createdDate>
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
</networks>"""

network_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/inventory/networks/1/">
  <active/>
  <createdDate>2010-09-15T21:41:40.142078+00:00</createdDate>
  <deviceName>eth0</deviceName>
  <dnsName>testnetwork.example.com</dnsName>
  <ipAddress>1.1.1.1</ipAddress>
  <ipv6Address/>
  <netmask>255.255.255.0</netmask>
  <networkId>1</networkId>
  <portType>lan</portType>
  <required/>
  <system href="http://testserver/api/inventory/systems/1"/>
</network>"""

network_put_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/inventory/networks/1/">
  <active/>
  <createdDate>2010-09-15T21:41:40.142078+00:00</createdDate>
  <deviceName>eth0</deviceName>
  <dnsName>new.com</dnsName>
  <ipAddress>2.2.2.2</ipAddress>
  <ipv6Address/>
  <netmask>255.255.255.0</netmask>
  <networkId>1</networkId>
  <portType>lan</portType>
  <required/>
  <system href="http://testserver/api/inventory/systems/1"/>
</network>"""

system_states_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemStates>
  <systemState id="http://testserver/api/inventory/systemStates/1/">
    <systemStateId>1</systemStateId>
    <description>Unmanaged</description>
    <name>unmanaged</name>
    <createdDate>2010-09-03T18:23:42.656549+00:00</createdDate>
  </systemState>
  <systemState id="http://testserver/api/inventory/systemStates/2/">
    <systemStateId>2</systemStateId>
    <description>Polling</description>
    <name>registered</name>
    <createdDate>2010-09-03T18:23:42.658249+00:00</createdDate>
  </systemState>
  <systemState id="http://testserver/api/inventory/systemStates/3/">
    <systemStateId>3</systemStateId>
    <description>Online</description>
    <name>responsive</name>
    <createdDate>2010-09-03T18:23:42.659883+00:00</createdDate>
  </systemState>
  <systemState id="http://testserver/api/inventory/systemStates/4/">
    <systemStateId>4</systemStateId>
    <description>Not responding: unknown</description>
    <name>non-responsive-unknown</name>
    <createdDate>2010-09-03T18:23:42.661629+00:00</createdDate>
  </systemState>
  <systemState id="http://testserver/api/inventory/systemStates/5/">
    <systemStateId>5</systemStateId>
    <description>Not responding: network unreachable</description>
    <name>non-responsive-net</name>
    <createdDate>2010-09-03T18:23:42.663290+00:00</createdDate>
  </systemState>
  <systemState id="http://testserver/api/inventory/systemStates/6/">
    <systemStateId>6</systemStateId>
    <description>Not responding: host unreachable</description>
    <name>non-responsive-host</name>
    <createdDate>2010-09-03T18:23:42.664943+00:00</createdDate>
    </systemState>
    <systemState id="http://testserver/api/inventory/systemStates/7/">
      <systemStateId>7</systemStateId>
      <description>Not responding: shutdown</description>
      <name>non-responsive-shutdown</name>
      <createdDate>2010-09-03T18:23:42.666612+00:00</createdDate>
    </systemState>
    <systemState id="http://testserver/api/inventory/systemStates/8/">
      <systemStateId>8</systemStateId>
      <description>Not responding: suspended</description>
      <name>non-responsive-suspended</name>
      <createdDate>2010-09-03T18:23:42.668266+00:00</createdDate>
    </systemState>
    <systemState id="http://testserver/api/inventory/systemStates/9/">
      <systemStateId>9</systemStateId>
      <description>Stale</description>
      <name>dead</name>
      <createdDate>2010-09-03T18:23:42.669899+00:00</createdDate>
    </systemState>
    <systemState id="http://testserver/api/inventory/systemStates/10/">
      <systemStateId>10</systemStateId>
      <description>Retired</description>
      <name>mothballed</name>
      <createdDate>2010-09-03T18:23:42.671647+00:00</createdDate>
    </systemState>
</systemStates>"""

system_state_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemState id="http://testserver/api/inventory/systemStates/1/">
  <systemStateId>1</systemStateId>
  <description>Unmanaged</description>
  <name>unmanaged</name>
  <createdDate>2010-09-03T18:23:42.656549+00:00</createdDate>
</systemState>"""

management_nodes_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNodes>
  <managementNode id="http://testserver/api/inventory/managementNodes/1">
    <agentPort/>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>test management node guuid</generatedUuid>
    <networks>
      <network id="http://testserver/api/inventory/networks/1/">
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
    <sslClientCertificate>test management node client cert</sslClientCertificate>
    <sslServerCertificate>test management node server cert</sslServerCertificate>
    <managingZone/>
    <hostname/>
    <name>test management node</name>
    <systemId>1</systemId>
    <launchingUser/>
    <managementNode>true</managementNode>
    <launchDate/>
    <local>true</local>
    <installedSoftware/>
    <jobs/>
    <description>test management node desc</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <targetSystemName/>
    <targetSystemDescription/>
    <targetSystemState/>
    <osMinorVersion/>
    <target/>
    <zone href="http://testserver/api/inventory/zones/2/"/>
    <systemPtr href="http://testserver/api/inventory/systems/1"/>
    <localUuid>test management node luuid</localUuid>
    <currentState id="http://testserver/api/inventory/systemStates/2/">
      <createdDate>%s</createdDate>
      <description>Polling</description>
      <name>registered</name>
      <systemStateId>2</systemStateId>
    </currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </managementNode>
</managementNodes>
"""

management_node_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode id="http://testserver/api/inventory/managementNodes/1">
  <agentPort/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>true</managementNode>
  <launchDate/>
  <local>true</local>
  <installedSoftware/>
  <jobs/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <createdDate>%s</createdDate>
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <zone href="http://testserver/api/inventory/zones/1/"/>
  <managingZone/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>True</managementNode>
  <local>True</local>
  <sslClientCertificate>test management node client cert</sslClientCertificate>
  <description>test management node desc</description>
  <localUuid>test management node luuid</localUuid>
  <osType/>
</managementNode>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode id="http://testserver/api/inventory/managementNodes/1">
  <agentPort/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <zone href="http://testserver/api/inventory/zones/1/"/>
  <nodeJid>abcd</nodeJid>
  <sslClientCertificate/>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <jobs/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>true</managementNode>
  <launchDate/>
  <local>true</local>
  <installedSoftware/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <target/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <createdDate>%s</createdDate>
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

management_node_zone_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode>
  <sslClientKey>test management node client key</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>test management node client cert</sslClientCertificate>
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
  <osType/>
</managementNode>"""

management_node_zone_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<managementNode id="http://testserver/api/inventory/managementNodes/1">
  <agentPort/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>test management node guuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <nodeJid>abcd</nodeJid>
  <sslClientCertificate/>
  <sslServerCertificate>test management node server cert</sslServerCertificate>
  <managingZone/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode>true</managementNode>
  <launchDate/>
  <local>true</local>
  <installedSoftware/>
  <jobs/>
  <description>test management node desc</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2/"/>
  <systemPtr href="http://testserver/api/inventory/systems/1"/>
  <localUuid>test management node luuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <createdDate>%s</createdDate>
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>%s</createdDate>
  <osType/>
</managementNode>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <eventTypes href="http://testserver/api/inventory/eventTypes/"/>
  <system id="http://testserver/api/inventory/systems/2">
    <agentPort/>
    <registrationDate/>
    <createdDate>2010-08-18T22:28:26+00:00</createdDate>
    <currentState id="http://testserver/api/inventory/systemStates/1/">
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <systemStateId>1</systemStateId>
    </currentState>
    <description>Local rPath Update Service</description>
    <generatedUuid/>
    <hostname/>
    <installedSoftware/>
    <jobs/>
    <launchDate/>
    <launchingUser/>
    <localUuid/>
    <managementNode>true</managementNode>
    <managingZone href="http://testserver/api/inventory/zones/1/"/>
    <name>rPath Update Service</name>
    <networks>
      <network id="http://testserver/api/inventory/networks/1/">
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
    <sslClientCertificate/>
    <sslServerCertificate/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <systemId>2</systemId>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <target/>
    <targetSystemId/>
    <targetSystemName/>
    <targetSystemDescription/>
    <targetSystemState/>
  </system>
  <system id="http://testserver/api/inventory/systems/3">
    <agentPort/>
    <registrationDate/>
    <createdDate>%s</createdDate>
    <currentState id="http://testserver/api/inventory/systemStates/2/">
      <description>Polling</description>
      <name>registered</name>
      <systemStateId>2</systemStateId>
    </currentState>
    <description>testsystemdescription</description>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <hostname/>
    <installedSoftware/>
    <jobs/>
    <launchDate/>
    <launchingUser/>
    <localUuid>testsystemlocaluuid</localUuid>
    <managementNode/>
    <managingZone/>
    <name>testsystemname</name>
    <networks>
      <network id="http://testserver/api/inventory/networks/2/">
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
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
    <systemId>3</systemId>
    <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
    <target/>
    <targetSystemId/>
    <targetSystemName/>
    <targetSystemDescription/>
    <targetSystemState/>
  </system>
</systems>
"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1">
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>testsystemgenerateduuid</generatedUuid>
    <networks>
      <network id="http://testserver/api/inventory/networks/1/">
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
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
    <targetSystemId/>
    <targetSystemName/>
    <targetSystemDescription/>
    <targetSystemState/>
    <osMinorVersion/>
    <managementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystemlocaluuid</localUuid>
    <currentState id="http://testserver/api/inventory/systemStates/2/">
      <description>Polling</description>
      <name>registered</name>
      <systemStateId>2</systemStateId>
    </currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
  <system id="http://testserver/api/inventory/systems/2">
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <registrationDate/>
    <generatedUuid>testsystem2generateduuid</generatedUuid>
    <networks>
      <network id="http://testserver/api/inventory/networks/1/">
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
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <launchDate/>
    <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
    <description>testsystemdescription</description>
    <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
    <targetSystemId/>
    <targetSystemName/>
    <targetSystemDescription/>
    <targetSystemState/>
    <osMinorVersion/>
    <managementNode/>
    <systemEvents href="http://testserver/api/inventory/systems/2/systemEvents/"/>
    <name>testsystemname</name>
    <localUuid>testsystem2localuuid</localUuid>
    <currentState id="http://testserver/api/inventory/systemStates/2/">
      <description>Polling</description>
      <name>registered</name>
      <systemStateId>2</systemStateId>
    </currentState>
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

systems_put_mothball_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <managementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/10/">
    <description>Retired</description>
    <name>mothballed</name>
    <systemStateId>10</systemStateId>
  </currentState>
</system>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agentPort/>
  <installedSoftware/>
  <jobs>
    <job id="http://testserver/api/inventory/jobs/1/">
      <jobId>1</jobId>
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <jobUuid>fixture-job-uuid1</jobUuid>
      <systems/>
    </job>
    <job id="http://testserver/api/inventory/jobs/2/">
      <jobId>2</jobId>
      <jobState>Queued</jobState>
      <jobType>immediate system poll</jobType>
      <jobUuid>fixture-job-uuid2</jobUuid>
      <systems/>
    </job>
    <job id="http://testserver/api/inventory/jobs/3/">
     <jobId>3</jobId>
      <jobState>Queued</jobState>
      <jobType>system poll</jobType>
      <jobUuid>fixture-job-uuid3</jobUuid>
      <systems/>
   </job>
    <job id="http://testserver/api/inventory/jobs/4/">
      <jobId>4</jobId>
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <jobUuid>fixture-job-uuid4</jobUuid>
      <systems/>
    </job>
  </jobs>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingZone/>
  <hostname/>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>1</systemId>
  <launchingUser/>
  <launchDate/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <managementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <osType/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agentPort/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode/>
  <launchDate/>
  <installedSoftware/>
  <jobs>
    <job id="http://testserver/api/inventory/jobs/1/">
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <systems/>
      <jobUuid>fixture-job-uuid1</jobUuid>
      <jobId>1</jobId>
    </job>
    <job id="http://testserver/api/inventory/jobs/2/">
      <jobState>Queued</jobState>
      <jobType>immediate system poll</jobType>
      <systems/>
      <jobUuid>fixture-job-uuid2</jobUuid>
      <jobId>2</jobId>
    </job>
    <job id="http://testserver/api/inventory/jobs/3/">
      <jobState>Queued</jobState>
      <jobType>system poll</jobType>
      <systems/>
      <jobUuid>fixture-job-uuid3</jobUuid>
      <jobId>3</jobId>
    </job>
    <job id="http://testserver/api/inventory/jobs/4/">
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <systems/>
      <jobUuid>fixture-job-uuid4</jobUuid>
      <jobId>4</jobId>
    </job>
  </jobs>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <target/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_post_no_network_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <name>testsystemname</name>
  <description>testsystemlocaluuid</description>
</system>"""

system_post_xml_dup = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <osType/>
</system>"""

system_post_xml_dup2 = system_post_xml_dup.replace(
    '<name>testsystemname</name>', 
    '<name>testsystemnameChanged</name>')

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agentPort/>
  <systemEvents href="http://testserver/api/inventory/systems/1/systemEvents/"/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>1</systemId>
  <launchingUser/>
  <managementNode/>
  <launchDate/>
  <installedSoftware/>
  <jobs>
    <job id="http://testserver/api/inventory/jobs/1/">
      <jobId>1</jobId>
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <jobUuid>fixture-job-uuid1</jobUuid>
      <systems/>
    </job>
    <job id="http://testserver/api/inventory/jobs/2/">
      <jobId>2</jobId>
      <jobState>Queued</jobState>
      <jobType>immediate system poll</jobType>
      <jobUuid>fixture-job-uuid2</jobUuid>
      <systems/>
    </job>
    <job id="http://testserver/api/inventory/jobs/3/">
      <jobId>3</jobId>
      <jobState>Queued</jobState>
      <jobType>system poll</jobType>
      <jobUuid>fixture-job-uuid3</jobUuid>
      <systems/>
    </job>
    <job id="http://testserver/api/inventory/jobs/4/">
      <jobId>4</jobId>
      <jobState>Queued</jobState>
      <jobType>system registration</jobType>
      <jobUuid>fixture-job-uuid4</jobUuid>
      <systems/>
    </job>
  </jobs>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/1/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <name>testsystemname</name>
  <target href="http://testserver/catalog/clouds/testtargettype/instances/testtargetname"/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
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
    <entry>Unable to register event 'system registration': no networking information</entry>
    <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
     <systemLogEntryId>2</systemLogEntryId>
   </systemLogEntry>
   <systemLogEntry>
     <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/4/systemLog/"/>
     <systemLogEntryId>3</systemLogEntryId>
   </systemLogEntry>
  <systemLogEntry>
    <entry>Unable to register event 'system registration': no networking information</entry>
    <systemLog href="http://testserver/api/inventory/systems/4/systemLog/"/>
    <systemLogEntryId>4</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>System added to inventory</entry>
    <systemLog href="http://testserver/api/inventory/systems/5/systemLog/"/>
    <systemLogEntryId>5</systemLogEntryId>
  </systemLogEntry>
  <systemLogEntry>
    <entry>Unable to register event 'system registration': no networking information</entry>
    <systemLog href="http://testserver/api/inventory/systems/5/systemLog/"/>
    <systemLogEntryId>6</systemLogEntryId>
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
      <isTopLevel>true</isTopLevel>
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
      <isTopLevel>false</isTopLevel>
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
      <isTopLevel>true</isTopLevel>
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
      <isTopLevel>false</isTopLevel>
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
  <agentPort/>
  %s
  <jobs/>
  <osMajorVersion/>
  <registrationDate/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <managingZone/>
  <hostname/>
  <networks>
    <network id="http://testserver/api/inventory/networks/2/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>3</systemId>
  <launchingUser/>
  <launchDate/>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <managementNode/>
  <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
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
  <eventUuid>testeventuuid</eventUuid>
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
  <networks>
    <network id="http://testserver/api/inventory/networks/1/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <systemId>2</systemId>
  <launchingUser/>
  <launchDate/>
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <description>testsystemdescription</description>
  <systemLog href="http://testserver/api/inventory/systems/2/systemLog/"/>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <managementNode/>
  <target/>
  <name/>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>2010-08-23T21:41:31.278455+00:00</createdDate>
  <osType/>
</system>
""" % installed_software_response_xml

system_available_updates_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/3">
  <agentPort/>
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
      <isTopLevel>true</isTopLevel>
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
      <isTopLevel>false</isTopLevel>
      <flavor>desktop is: x86_64</flavor>
    </trove>
  </installedSoftware>
  <jobs/>
  <systemEvents href="http://testserver/api/inventory/systems/3/systemEvents/"/>
  <osMajorVersion/>
  <generatedUuid>testsystemgenerateduuid</generatedUuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/2/">
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
  <sslClientCertificate>testsystemsslclientcertificate</sslClientCertificate>
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <managingZone/>
  <hostname/>
  <systemId>3</systemId>
  <launchingUser/>
  <managementNode/>
  <launchDate/>
  <systemLog href="http://testserver/api/inventory/systems/3/systemLog/"/>
  <registrationDate/>
  <description>testsystemdescription</description>
  <targetSystemId/>
  <targetSystemName/>
  <targetSystemDescription/>
  <targetSystemState/>
  <osMinorVersion/>
  <target/>
  <name>testsystemname</name>
  <localUuid>testsystemlocaluuid</localUuid>
  <currentState id="http://testserver/api/inventory/systemStates/2/">
    <description>Polling</description>
    <name>registered</name>
    <systemStateId>2</systemStateId>
  </currentState>
  <createdDate>2010-08-27T12:21:59.800269+00:00</createdDate>
  <osType/>
</system>
"""

x509_pem = """\
-----BEGIN CERTIFICATE-----
MIIDSTCCAjGgAwIBAgIBATANBgkqhkiG9w0BAQUFADBhMTEwLwYDVQQKEyhyQnVp
bGRlciBMb3ctR3JhZGUgQ2VydGlmaWNhdGUgQXV0aG9yaXR5MSwwKgYDVQQLEyND
cmVhdGVkIGF0IDIwMTAtMDktMDIgMTE6MTg6NTMtMDQwMDAeFw0xMDA5MDExNTE4
NTNaFw0yMDA5MDExNTE4NTNaMF0xLTArBgNVBAoTJHJCdWlsZGVyIFJlcGVhdGVy
IENsaWVudCBDZXJ0aWZpY2F0ZTEsMCoGA1UECxMjQ3JlYXRlZCBhdCAyMDEwLTA5
LTAyIDExOjE4OjUzLTA0MDAwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
AQCgz+pOK5ROa/+PJo9/3glqvqchCBJIOYiygGpUMGq1p/HKspN08RsuHPL4/1Dd
h+AGMQndojaumIvuDW/3eP9AgXfJZa6YDjNmhmGTBOqCickOoc/vGmdFnsi6cNCT
ClBR4MvW770h1yQdSgtUszyixTBLn+5yB5oIIKCXVMxuh63XhTa9TVsk5HRIpAW9
ZVIaWhRU/QQhYt5qPE7OoePKRkUS3zNXK/LAgPEayzPJbUT4AHku33Ps8dCyVBDC
oOgKOu0FSGqAqleprDPaQslWx0bjx7kQMObt7ptTTPWGV+T0TSIrz8ab370PYY7e
KsNXS+Ad9yiZCbcrg5uMYrr7AgMBAAGjEDAOMAwGA1UdEwEB/wQCMAAwDQYJKoZI
hvcNAQEFBQADggEBAAEOZy8q2W4eRS7jjOHVjKMNBl7qVQafRCApjZmmmHcqWLF9
oA+wsbuYgbTHYPZ91johrKJx2D7KUj+dhTHLN3QmCSRwschUTLL8SSTlncT6NI4V
nYvxBhgh45N+RVmk/hWSeNGHPZrHKSnnFyxRWUooDontBoUTlmQP9v6CXGxwFBpb
k+BIkRElpceL73AMmiquPCUNIeMmGZqQivLvaIzowREQCuXNorJgMAdG5xWddO3H
/duKEYsL6aGrEG9mw7CAxzA0fcq5T9YFq90nd9E0g3IhfiAWvsrInJmH0c7DhaZ/
2r9WWECYqxWkHMLsW6PVA0pVTL/XoicHiu6NTac=
-----END CERTIFICATE-----"""

pkey_pem = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAoM/qTiuUTmv/jyaPf94Jar6nIQgSSDmIsoBqVDBqtafxyrKT
dPEbLhzy+P9Q3YfgBjEJ3aI2rpiL7g1v93j/QIF3yWWumA4zZoZhkwTqgonJDqHP
7xpnRZ7IunDQkwpQUeDL1u+9IdckHUoLVLM8osUwS5/ucgeaCCCgl1TMboet14U2
vU1bJOR0SKQFvWVSGloUVP0EIWLeajxOzqHjykZFEt8zVyvywIDxGsszyW1E+AB5
Lt9z7PHQslQQwqDoCjrtBUhqgKpXqawz2kLJVsdG48e5EDDm7e6bU0z1hlfk9E0i
K8/Gm9+9D2GO3irDV0vgHfcomQm3K4ObjGK6+wIDAQABAoIBADDoiz5TCrv/JK6I
78PX581LRtFI/yZwOR7w52XLg+jTtzoKrcY3Pij8LPmFzTZTCNNZPsLlfvQC+Svh
clg1uIwJ1ECwaDVevEtGO47XQ+uHtFp65B64TQhjjnEFtqnBzUPZtqUcLM2J/TXb
Oy77hEmM529YqNCNd09ZfP4JkFNc/PVauJeHfjikLtTCPQxfIL1/SryCCxhpGdOJ
BYY45enPurzeeTosddxhh0zCfTbjDkZIvC6j0gapMtQ3y0HVu4rqZApZAtqRRkol
3ThT4f94gOiMUpa3n5GqdeQztBziP2tm0dfqajvY8DkG4l8cLs5JMV3ybzuRjO7D
nK+ioWECgYEA1Q9q15QVf8SABn4Hx7glwR3y9US2oQxnzD8FSyHys6ayXqrIBRTm
ctY8fqx5FaAgLRleYrqppAEFHnyv0rNuj5uBG4Vv7hPVFMMB2IjX6Go3y4Kp2Cji
E0exfaED1fOVF6Qg3YMrlLN9UQDWDVXtowmmf1MZeKJrbHIm9G7/tbcCgYEAwTjS
uv1yJQvMeCgzhHkYjwaTGFYIIENrwh5v+aqL/qFfisxBb2TGCeWMenel4nI/7Sj8
Ks5skazLilMY0XvXZQLQb8Z46ejz3qAF90Nt7mR8+3Fi/RG3CV7nlTYKi4EBoRwa
A6J5HYjJbWsvWPjRun+VC5/RCLaLRt3vBruUBN0CgYBWbXeg1bBW8QYiHBPZ34hp
K1X4SpRvBhJBFzt1e+LxH2jx4ANdlFnbMa6+kAZaUGddBBJ2qFPSdJt3/4pvRVxP
IvyfhmSeRitEzco85V34KMZTZsCxL/xtZ8LHPH7K1pGfUnQGh4QxQRJPvrAWHspU
PcDtm28UsYY0KqZEt5ZBRwKBgQCxF4V8wIH3lkLG9gGRrvNlUx9KNL+p4mFHP2Jd
r4Qz0m+g5OgsUm537527OSIe05vnn6LPEPbM5VR/6P1cMmcOO3ASohN8P3gUWRJe
t7xvvEYYpqmVTME3o3YZebhcd9aodPsazbS37wC+enig0RxYFErkpouNstEgGJTU
1OMrOQKBgGj8bASJ+BypTtg8xnac5FuzEPr0ksjz+FaY+NGeXmfqCxdTvUs0Ue25
Aj/9jaPTk+mjBIgXSVEHkJCtxfGZWYFx/eNItfaAAfZVX68txm5Hyp2J6Equnr82
9GYZo4+j1V1Ld2WUxY+jXJdJetbrPjU4Bq8M+etypQrNJXrX/DD4
-----END RSA PRIVATE KEY-----"""
