#!/usr/bin/python

inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <log href="http://testserver/api/inventory/log/"/>
  <systems href="http://testserver/api/inventory/systems/"/>
</inventory>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1/">
    <activated>True</activated>
    <sslClientKey>testsystemsslclientkey</sslClientKey>
    <osMajorVersion/>
    <activationDate>%s</activationDate>
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
    <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
    <state>activated</state>
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
    <createdDate>%s</createdDate>
    <osType/>
  </system>
</systems>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1/">
  <activated>True</activated>
  <sslClientKey>testsystemsslclientkey</sslClientKey>
  <osMajorVersion/>
  <activationDate>%s</activationDate>
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
  <sslServerCertificate>testsystemsslservercertificate</sslServerCertificate>
  <state>activated</state>
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
  <createdDate>%s</createdDate>
  <osType/>
</system>"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvents>
    <systemEvent id="http://testserver/api/inventory/systemEvents/1/">
        <priority>50</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>1</systemEventId>
        <timeCreated>%s</timeCreated>
    </systemEvent>
    <systemEvent id="http://testserver/api/inventory/systemEvents/2/">
        <priority>100</priority>
        <timeEnabled>%s</timeEnabled>
        <systemEventId>2</systemEventId>
        <timeCreated>%s</timeCreated>
    </systemEvent>
</systemEvents>
"""

system_event_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systemEvent id="http://testserver/api/inventory/systemEvents/1/">
    <priority>50</priority>
    <timeEnabled>%s</timeEnabled>
    <systemEventId>1</systemEventId>
    <timeCreated>%s</timeCreated>
</systemEvent>
"""
