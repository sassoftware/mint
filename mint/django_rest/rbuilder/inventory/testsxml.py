#!/usr/bin/python

inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <event_types href="http://testserver/api/inventory/event_types"/>
  <image_import_metadata_descriptor href="http://testserver/api/inventory/image_import_metadata_descriptor"/>
  <infrastructure_systems href="http://testserver/api/inventory/infrastructure_systems"/>
  <inventory_systems href="http://testserver/api/inventory/inventory_systems"/>
  <job_states href="http://testserver/api/inventory/job_states"/>
  <log href="http://testserver/api/inventory/log"/>
  <zones href="http://testserver/api/inventory/zones"/>
  <management_nodes href="http://testserver/api/inventory/management_nodes"/>
  <management_interfaces href="http://testserver/api/inventory/management_interfaces"/>
  <system_types href="http://testserver/api/inventory/system_types"/>
  <systems href="http://testserver/api/inventory/systems"/>
  <system_states href="http://testserver/api/inventory/system_states"/>
  <networks href="http://testserver/api/inventory/networks"/>
</inventory>"""

event_type_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/inventory/event_types/1">
  <description>System registration</description>
  <priority>110</priority>
  <event_type_id>1</event_type_id>
  <name>system registration</name>
  <system_events/>
</event_type>"""

event_types_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_types>
  <event_type id="http://testserver/api/inventory/event_types/1">
    <name>system registration</name>
    <priority>110</priority>
    <event_type_id>1</event_type_id>
    <description>System registration</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/2">
    <name>immediate system poll</name>
    <priority>105</priority>
    <event_type_id>2</event_type_id>
    <description>On-demand system synchronization</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/3">
    <name>system poll</name>
    <priority>50</priority>
    <event_type_id>3</event_type_id>
    <description>System synchronization</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/4">
    <description>Scheduled system update</description>
    <event_type_id>4</event_type_id>
    <name>system apply update</name>
    <priority>50</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/5">
    <description>System update</description>
    <event_type_id>5</event_type_id>
    <name>immediate system apply update</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/6">
    <description>Scheduled system shutdown</description>
    <event_type_id>6</event_type_id>
    <name>system shutdown</name>
    <priority>50</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/7">
    <description>System shutdown</description>
    <event_type_id>7</event_type_id>
    <name>immediate system shutdown</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/8">
    <description>Launched system network data discovery</description>
    <event_type_id>8</event_type_id>
    <name>system launch wait</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/9">
    <description>System management interface detection</description>
    <event_type_id>9</event_type_id>
    <name>system detect management interface</name>
    <priority>50</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/10">
    <description>On-demand system management interface detection</description>
    <event_type_id>10</event_type_id>
    <name>immediate system detect management interface</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/inventory/event_types/11">
    <description>Update system configuration</description>
    <event_type_id>11</event_type_id>
    <name>immediate system configuration</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
</event_types>"""

event_type_put_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/inventory/event_types/1">
  <description>System registration</description>
  <priority>1</priority>
  <event_type_id>1</event_type_id>
  <name>system registration</name>
  <system_events/>
</event_type>"""

event_type_put_name_change_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/inventory/event_types/1">
  <description>System registration</description>
  <priority>110</priority>
  <event_type_id>1</event_type_id>
  <name>foobar</name>
  <system_events/>
</event_type>"""

zones_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zones>
  <zone id="http://testserver/api/inventory/zones/1">
    <description>Some local zone</description>
    <created_date>%s</created_date>
    <name>Local Zone</name>
    <management_nodes/>
    <zone_id>1</zone_id>
  </zone>
</zones>
"""

zone_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/1">
  <description>Some local zone</description>
  <created_date>%s</created_date>
  <name>Local Zone</name>
  <management_nodes/>
  <zone_id>1</zone_id>
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
<zone id="http://testserver/api/inventory/zones/1">
  <description>Some local zone</description>
  <created_date>%s</created_date>
  <name>Local Zone</name>
  <management_nodes/>
  <zone_id>1</zone_id>
</zone>
"""

zone_post_2_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone>
  <description>Some other zone</description>
  <name>someother zone</name>
</zone>
"""

zone_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/inventory/zones/1">
  <description>zoneputdesc</description>
  <name>zoneputname</name>
  <created_date>%s</created_date>
</zone>
"""

management_interfaces_xml="""\
<?xml version="1.0"?>
<management_interfaces>
  <management_interface id="http://testserver/api/inventory/management_interfaces/1">
    <description>bar</description>
    <management_interface_id>1</management_interface_id>
    <created_date>2010-10-06T00:11:27.828160+00:00</created_date>
    <credentials_descriptor><foo/></credentials_descriptor>
    <port>8000</port>
    <name>foo</name>
    <credentials_readonly/>
  </management_interface>
</management_interfaces>
"""

management_interface_xml="""\
<?xml version="1.0"?>
<management_interface id="http://testserver/api/inventory/management_interfaces/1">
  <description>bar</description>
  <management_interface_id>1</management_interface_id>
  <created_date>2010-10-06T00:11:27.828160+00:00</created_date>
  <credentials_descriptor><foo/></credentials_descriptor>
  <port>8000</port>
  <name>foo</name>
  <credentials_readonly/>
</management_interface>
"""

management_interface_put_xml="""\
<?xml version="1.0"?>
<management_interface id="http://testserver/api/inventory/management_interfaces/1/">
  <systems/>
  <description>bar</description>
  <management_interface_id>1</management_interface_id>
  <created_date>2010-10-06T00:11:27.828160+00:00</created_date>
  <credentials_descriptor><foo/></credentials_descriptor>
  <port>123</port>
  <name>thisnameshouldnotstick</name>
</management_interface>
"""

system_types_xml="""\
<?xml version="1.0"?>
<system_types>
  <system_type id="http://testserver/api/inventory/system_types/1">
    <system_type_id>1</system_type_id>
    <infrastructure>false</infrastructure>
    <description>bar</description>
    <name>foo</name>
    <created_date>2010-10-07T00:42:33.634913+00:00</created_date>
    <creation_descriptor>
      <foo/>
    </creation_descriptor>
  </system_type>
</system_types>"""

system_type_xml="""\
<?xml version="1.0"?>
<system_type id="http://testserver/api/inventory/system_types/1">
  <system_type_id>1</system_type_id>
  <infrastructure>false</infrastructure>
  <description>bar</description>
  <name>foo</name>
  <created_date>2010-10-07T00:42:33.634913+00:00</created_date>
  <creation_descriptor>
    <foo/>
  </creation_descriptor>
</system_type>"""

system_types_put_xml="""\
<?xml version="1.0"?>
<system_type id="http://testserver/api/inventory/system_types/1">
  <system_type_id>1</system_type_id>
  <infrastructure>True</infrastructure>
  <description>bar</description>
  <name>thisnameshouldnotstick</name>
  <created_date>2010-10-07T00:42:33.634913+00:00</created_date>
</system_type>"""

system_type_systems_xml="""
<?xml version="1.0"?>
<systems>
  <event_types href="http://testserver/api/inventory/system_types/1/event_types"/>
  <system id="http://testserver/api/inventory/systems/3">
    <agent_port>5989</agent_port>
    <appliance/>
    <credentials href="http://testserver/api/inventory/systems/3/credentials"/>
    <configuration href="http://testserver/api/inventory/systems/3/configuration"/>
    <configuration_descriptor href="http://testserver/api/inventory/systems/3/configuration_descriptor"/>
    <current_state id="http://testserver/api/inventory/system_states/2">
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>False</has_active_jobs>
    <has_running_jobs>False</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/inventory/systems/3/installed_software"/>
    <jobs id="http://testserver/api/inventory/systems/3/jobs">
      <completed_jobs href="http://testserver/api/inventory/systems/3/job_states/3/jobs"/>
      <failed_jobs href="http://testserver/api/inventory/systems/3/job_states/4/jobs"/>
      <queued_jobs href="http://testserver/api/inventory/systems/3/job_states/1/jobs"/>
      <running_jobs href="http://testserver/api/inventory/systems/3/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <major_version/>
    <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <networks>
      <network id="http://testserver/api/inventory/networks/2">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <required/>
        <system href="http://testserver/api/inventory/systems/3"/>
      </network>
    </networks>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <stage/>
    <system_events href="http://testserver/api/inventory/systems/3/system_events"/>
    <system_id>3</system_id>
    <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
    <target/>
    <target_system_description/>
    <target_system_id/>
    <target_system_name/>
    <target_system_state/>
    <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  </system>
</systems>
"""

networks_xml = """\
<?xml version="1.0"?>
<networks>
  <systems href="http://testserver/api/inventory/systems"/>
  <network id="http://testserver/api/inventory/networks/1">
    <active/>
    <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
    <device_name>eth0</device_name>
    <dns_name>testnetwork.example.com</dns_name>
    <ip_address>1.1.1.1</ip_address>
    <ipv6_address/>
    <netmask>255.255.255.0</netmask>
    <network_id>1</network_id>
    <port_type>lan</port_type>
    <required/>
    <system href="http://testserver/api/inventory/systems/1"/>
  </network>
</networks>"""

network_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/inventory/networks/1">
  <active/>
  <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
  <device_name>eth0</device_name>
  <dns_name>testnetwork.example.com</dns_name>
  <ip_address>1.1.1.1</ip_address>
  <ipv6_address/>
  <netmask>255.255.255.0</netmask>
  <network_id>1</network_id>
  <port_type>lan</port_type>
  <required/>
  <system href="http://testserver/api/inventory/systems/1"/>
</network>"""

network_put_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/inventory/networks/1">
  <active/>
  <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
  <device_name>eth0</device_name>
  <dns_name>new.com</dns_name>
  <ip_address>2.2.2.2</ip_address>
  <ipv6_address/>
  <netmask>255.255.255.0</netmask>
  <network_id>1</network_id>
  <port_type>lan</port_type>
  <required/>
  <system href="http://testserver/api/inventory/systems/1"/>
</network>"""

system_states_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_states>
  <system_state id="http://testserver/api/inventory/system_states/1">
    <system_state_id>1</system_state_id>
    <description>Unmanaged</description>
    <name>unmanaged</name>
    <created_date>2010-09-03T18:23:42.656549+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/2">
    <system_state_id>2</system_state_id>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <created_date>2010-09-03T18:23:42.658249+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/3">
    <system_state_id>3</system_state_id>
    <description>Online</description>
    <name>responsive</name>
    <created_date>2010-09-03T18:23:42.659883+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/4">
    <system_state_id>4</system_state_id>
    <description>Not responding: Unknown</description>
    <name>non-responsive-unknown</name>
    <created_date>2010-09-03T18:23:42.661629+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/5">
    <system_state_id>5</system_state_id>
    <description>Not responding: Network unreachable</description>
    <name>non-responsive-net</name>
    <created_date>2010-09-03T18:23:42.663290+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/6">
    <system_state_id>6</system_state_id>
    <description>Not responding: Host unreachable</description>
    <name>non-responsive-host</name>
    <created_date>2010-09-03T18:23:42.664943+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/inventory/system_states/7">
      <system_state_id>7</system_state_id>
      <description>Not responding: Shutdown</description>
      <name>non-responsive-shutdown</name>
      <created_date>2010-09-03T18:23:42.666612+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/inventory/system_states/8">
      <system_state_id>8</system_state_id>
      <description>Not responding: Suspended</description>
      <name>non-responsive-suspended</name>
      <created_date>2010-09-03T18:23:42.668266+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/inventory/system_states/9">
      <system_state_id>9</system_state_id>
      <description>Stale</description>
      <name>dead</name>
      <created_date>2010-09-03T18:23:42.669899+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/inventory/system_states/10">
      <system_state_id>10</system_state_id>
      <description>Retired</description>
      <name>mothballed</name>
      <created_date>2010-09-03T18:23:42.671647+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/inventory/system_states/11">
    <description>Unmanaged: Invalid credentials</description>
    <name>unmanaged-credentials</name>
    <system_state_id>11</system_state_id>
  </system_state>
  <system_state id="http://testserver/api/inventory/system_states/12">
    <description>Not responding: Invalid credentials</description>
    <name>non-responsive-credentials</name>
    <system_state_id>12</system_state_id>
  </system_state>
</system_states>"""

system_state_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_state id="http://testserver/api/inventory/system_states/1">
  <system_state_id>1</system_state_id>
  <description>Unmanaged</description>
  <name>unmanaged</name>
  <created_date>2010-09-03T18:23:42.656549+00:00</created_date>
</system_state>"""

management_nodes_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_nodes>
  <management_node id="http://testserver/api/inventory/management_nodes/1">
    <agent_port>5989</agent_port>
    <appliance/>
    <credentials href="http://testserver/api/inventory/management_nodes/1/credentials"/>
    <configuration href="http://testserver/api/inventory/management_nodes/1/configuration"/>
    <configuration_descriptor href="http://testserver/api/inventory/management_nodes/1/configuration_descriptor"/>
    <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <generated_uuid>test management node guuid</generated_uuid>
    <has_active_jobs>False</has_active_jobs>
    <has_running_jobs>False</has_running_jobs>
    <networks>
      <network id="http://testserver/api/inventory/networks/1">
        <active/>
        <created_date>%s</created_date>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>2.2.2.2</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>1</network_id>
        <port_type>lan</port_type>
        <required/>
        <system href="http://testserver/api/inventory/systems/1"/>
      </network>
    </networks>
    <node_jid>superduperjid2@rbuilder.rpath</node_jid>
    <ssl_client_certificate>test management node client cert</ssl_client_certificate>
    <ssl_server_certificate>test management node server cert</ssl_server_certificate>
    <stage/>
    <managing_zone href="http://testserver/api/inventory/zones/2">Local Zone</managing_zone>
    <hostname/>
    <name>test management node</name>
    <system_id>1</system_id>
    <launching_user/>
    <launch_date/>
    <local>true</local>
    <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
    <jobs id="http://testserver/api/inventory/systems/1/jobs">
      <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
      <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
      <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
      <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
    </jobs>
    <description>test management node desc</description>
    <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type href="http://testserver/api/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
    <target/>
    <zone href="http://testserver/api/inventory/zones/2"/>
    <system_ptr href="http://testserver/api/inventory/systems/1"/>
    <local_uuid>test management node luuid</local_uuid>
    <major_version/>
    <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/inventory/system_states/2">
      <created_date>%s</created_date>
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
  </management_node>
</management_nodes>
"""

management_node_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/inventory/management_nodes/1">
  <agent_port>5989</agent_port> 
  <appliance/>
  <credentials href="http://testserver/api/inventory/management_nodes/1/credentials"/>
  <configuration href="http://testserver/api/inventory/management_nodes/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/management_nodes/1/configuration_descriptor"/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <node_jid>superduperjid2@rbuilder.rpath</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/2">Local Zone</managing_zone>
  <hostname/>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
  </jobs>
  <description>test management node desc</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2"/>
  <system_ptr href="http://testserver/api/inventory/systems/1"/>
  <local_uuid>test management node luuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <created_date>%s</created_date>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</management_node>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node>
  <ssl_client_key>test management node client key</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <stage/>
  <zone href="http://testserver/api/inventory/zones/1"/>
  <managing_zone href="http://testserver/api/inventory/zones/1"/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>True</local>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <description>test management node desc</description>
  <local_uuid>test management node luuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
</management_node>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/inventory/management_nodes/1">
  <agent_port>5989</agent_port> 
  <appliance/>
  <credentials href="http://testserver/api/inventory/management_nodes/1/credentials"/>
  <configuration href="http://testserver/api/inventory/management_nodes/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/management_nodes/1/configuration_descriptor"/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <zone href="http://testserver/api/inventory/zones/1"/>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate/>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
  </jobs>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <description>test management node desc</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <system_ptr href="http://testserver/api/inventory/systems/1"/>
  <local_uuid>test management node luuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <created_date>%s</created_date>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</management_node>"""

management_node_zone_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node>
  <ssl_client_key>test management node client key</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <stage/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>True</local>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <description>test management node desc</description>
  <zone href="http://testserver/api/inventory/zones/2"/>
  <local_uuid>test management node luuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <managing_zone href="http://testserver/api/inventory/zones/1"/>
</management_node>"""

management_node_zone_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/inventory/management_nodes/1">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/management_nodes/1/credentials"/>
  <configuration href="http://testserver/api/inventory/management_nodes/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/management_nodes/1/configuration_descriptor"/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate/>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
  </jobs>
  <description>test management node desc</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <zone href="http://testserver/api/inventory/zones/2"/>
  <system_ptr href="http://testserver/api/inventory/systems/1"/>
  <local_uuid>test management node luuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <created_date>%s</created_date>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</management_node>"""

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <event_types href="http://testserver/api/inventory/event_types"/>
  <system id="http://testserver/api/inventory/systems/2">
    <agent_port/>
    <appliance/>
    <credentials href="http://testserver/api/inventory/systems/2/credentials"/>
    <configuration href="http://testserver/api/inventory/systems/2/configuration"/>
    <configuration_descriptor href="http://testserver/api/inventory/systems/2/configuration_descriptor"/>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <created_date>2010-08-18T22:28:26+00:00</created_date>
    <current_state id="http://testserver/api/inventory/system_states/1">
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <system_state_id>1</system_state_id>
    </current_state>
    <description>Local rPath Update Service</description>
    <generated_uuid/>
    <has_active_jobs>False</has_active_jobs>
    <has_running_jobs>False</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/inventory/systems/2/installed_software"/>
    <jobs id="http://testserver/api/inventory/systems/2/jobs">
      <completed_jobs href="http://testserver/api/inventory/systems/2/job_states/3/jobs"/>
      <failed_jobs href="http://testserver/api/inventory/systems/2/job_states/4/jobs"/>
      <queued_jobs href="http://testserver/api/inventory/systems/2/job_states/1/jobs"/>
      <running_jobs href="http://testserver/api/inventory/systems/2/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid/>
    <major_version/>
    <management_interface/>
    <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
    <name>rPath Update Service</name>
    <networks>
      <network id="http://testserver/api/inventory/networks/1">
        <active/>
        <created_date>2010-08-18T22:28:26+00:00</created_date>
        <device_name/>
        <dns_name>127.0.0.1</dns_name>
        <ip_address/>
        <ipv6_address/>
        <netmask/>
        <network_id>1</network_id>
        <port_type/>
        <required/>
        <system href="http://testserver/api/inventory/systems/2"/>
      </network>
    </networks>
    <ssl_client_certificate/>
    <ssl_server_certificate/>
    <stage/>
    <system_events href="http://testserver/api/inventory/systems/2/system_events"/>
    <system_id>2</system_id>
    <system_log href="http://testserver/api/inventory/systems/2/system_log"/>
    <target/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type href="http://testserver/api/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  </system>
  <system id="http://testserver/api/inventory/systems/3">
    <agent_port>5989</agent_port>
    <appliance/>
    <credentials href="http://testserver/api/inventory/systems/3/credentials"/>
    <configuration href="http://testserver/api/inventory/systems/3/configuration"/>
    <configuration_descriptor href="http://testserver/api/inventory/systems/3/configuration_descriptor"/>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <created_date>%s</created_date>
    <current_state id="http://testserver/api/inventory/system_states/2">
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>False</has_active_jobs>
    <has_running_jobs>False</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/inventory/systems/3/installed_software"/>
    <jobs id="http://testserver/api/inventory/systems/3/jobs">
      <completed_jobs href="http://testserver/api/inventory/systems/3/job_states/3/jobs"/>
      <failed_jobs href="http://testserver/api/inventory/systems/3/job_states/4/jobs"/>
      <queued_jobs href="http://testserver/api/inventory/systems/3/job_states/1/jobs"/>
      <running_jobs href="http://testserver/api/inventory/systems/3/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <major_version/>
    <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <networks>
      <network id="http://testserver/api/inventory/networks/2">
        <active/>
        <created_date>%s</created_date>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <required/>
        <system href="http://testserver/api/inventory/systems/3"/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <stage/>
    <system_events href="http://testserver/api/inventory/systems/3/system_events"/>
    <system_id>3</system_id>
    <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
    <target/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  </system>
</systems>
"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/inventory/systems/1">
    <ssl_client_key>testsystemsslclientkey</ssl_client_key>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <networks>
      <network id="http://testserver/api/inventory/networks/1">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>1</network_id>
        <port_type>lan</port_type>
        <required/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <stage/>
    <launch_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <description>testsystemdescription</description>
    <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/inventory/system_types/1">Inventory</system_type>
    <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
    <name>testsystemname</name>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <major_version/>
    <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/inventory/system_states/2">
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
  </system>
  <system id="http://testserver/api/inventory/systems/2">
    <ssl_client_key>testsystemsslclientkey</ssl_client_key>
    <out_of_date>False</out_of_date>
    <registration_date/>
    <generated_uuid>testsystem2generateduuid</generated_uuid>
    <networks>
      <network id="http://testserver/api/inventory/networks/1">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork2.example.com</dns_name>
        <ip_address>2.2.2.2</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <required/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <stage/>
    <launch_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <description>testsystemdescription</description>
    <system_log href="http://testserver/api/inventory/systems/2/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
    <system_events href="http://testserver/api/inventory/systems/2/system_events"/>
    <name>testsystemname</name>
    <local_uuid>testsystem2localuuid</local_uuid>
    <major_version/>
    <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/inventory/system_states/2">
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
  </system>
</systems>"""

systems_put_mothball_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/10">
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>10</system_state_id>
  </current_state>
</system>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/1/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/1/configuration_descriptor"/>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
  </jobs>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>True</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</system>"""

system_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
</system>"""

system_mgmt_interface_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/2">Windows Management Instrumentation (WMI)</management_interface>
</system>"""

system_delete_mgmt_interface_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/1/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/1/configuration_descriptor"/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>True</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
  </jobs>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <target/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</system>"""

system_post_no_network_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <name>testsystemname</name>
  <description>testsystemlocaluuid</description>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
</system>"""

system_post_xml_dup = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <required/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
</system>"""

system_post_xml_dup2 = system_post_xml_dup.replace(
    '<name>testsystemname</name>', 
    '<name>testsystemnameChanged</name>')

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/1">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/1/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/1/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/1/configuration_descriptor"/>
  <system_events href="http://testserver/api/inventory/systems/1/system_events"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>True</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/1"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>1</system_id>
  <launching_user/>
  <launch_date/>
  <installed_software id="http://testserver/api/inventory/systems/1/installed_software"/>
  <jobs id="http://testserver/api/inventory/systems/1/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/1/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/1/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/1/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/1/job_states/2/jobs"/>
   </jobs>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <target href="http://testserver/catalog/clouds/testtargettype/instances/testtargetname">testtargetname</target>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%s</created_date>
</system>
"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_events>
    <system_event id="http://testserver/api/inventory/system_events/1">
        <event_data/>
        <event_type href="http://testserver/api/inventory/event_types/3"/>
        <system href="http://testserver/api/inventory/systems/3"/>
        <time_created>%s</time_created>
        <priority>50</priority>
        <time_enabled>%s</time_enabled>
        <system_event_id>1</system_event_id>
    </system_event>
    <system_event id="http://testserver/api/inventory/system_events/2">
        <event_data/>
        <event_type href="http://testserver/api/inventory/event_types/1"/>
        <system href="http://testserver/api/inventory/systems/3"/>
        <time_created>%s</time_created>
        <priority>110</priority>
        <time_enabled>%s</time_enabled>
        <system_event_id>2</system_event_id>
    </system_event>
</system_events>
"""

system_event_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event id="http://testserver/api/inventory/system_events/1">
    <event_data/>
    <event_type href="http://testserver/api/inventory/event_types/3"/>
    <system href="http://testserver/api/inventory/systems/3"/>
    <time_created>%s</time_created>
    <priority>50</priority>
    <time_enabled>%s</time_enabled>
    <system_event_id>1</system_event_id>
</system_event>
"""

system_event_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type href="http://testserver/api/inventory/event_types/3"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_poll_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type href="http://testserver/api/inventory/event_types/2"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_update_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type href="http://testserver/api/inventory/event_types/5"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_shutdown_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type href="http://testserver/api/inventory/event_types/7"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_registration_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type href="http://testserver/api/inventory/event_types/1"/>
    <system href="http://testserver/api/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_log id="http://testserver/api/inventory/systems/1/system_log">
  <system_log_entries>
    <system_log_entry>
      <entry>System added to inventory</entry>
      <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
      <system_log_entry_id>1</system_log_entry_id>
    </system_log_entry>
    <system_log_entry>
      <entry>System registered via rpath-tools</entry>
      <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
      <system_log_entry_id>2</system_log_entry_id>
    </system_log_entry>
    <system_log_entry>
      <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
      <system_log_entry_id>3</system_log_entry_id>
    </system_log_entry>
    <system_log_entry>
      <system_log href="http://testserver/api/inventory/systems/1/system_log"/>
      <system_log_entry_id>4</system_log_entry_id>
    </system_log_entry>
  </system_log_entries>
  <system_log_id>1</system_log_id>
  <system href="http://testserver/api/inventory/systems/1"/>
</system_log>
"""

systems_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems_log>
  <system_log_entry>
    <entry>System added to inventory</entry>
    <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
    <system_log_entry_id>1</system_log_entry_id>
  </system_log_entry>
   <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
     <system_log_entry_id>2</system_log_entry_id>
   </system_log_entry>
   <system_log_entry>
     <entry>System added to inventory</entry>
    <system_log href="http://testserver/api/inventory/systems/4/system_log"/>
     <system_log_entry_id>3</system_log_entry_id>
   </system_log_entry>
  <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log href="http://testserver/api/inventory/systems/4/system_log"/>
    <system_log_entry_id>4</system_log_entry_id>
  </system_log_entry>
  <system_log_entry>
    <entry>System added to inventory</entry>
    <system_log href="http://testserver/api/inventory/systems/5/system_log"/>
    <system_log_entry_id>5</system_log_entry_id>
  </system_log_entry>
  <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log href="http://testserver/api/inventory/systems/5/system_log"/>
    <system_log_entry_id>6</system_log_entry_id>
  </system_log_entry>
</systems_log>
"""

get_installed_software_xml = """\
  <installed_software id="http://testserver/api/inventory/systems/3/installed_software/">
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%%3D/clover.eng.rpath.com%%40rpath%%3Aclover-1-devel/1-2-1%%5B%%7E%%21dom0%%2C%%7E%%21domU%%2Cvmware%%2C%%7E%%21xen%%20is%%3A%%20x86%%28i486%%2Ci586%%2Ci686%%2Csse%%2Csse2%%29%%5D">
      <available_updates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567891.13</ordering>
          <revision>1-3-1</revision>
          <version_id>2</version_id>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567892.14</ordering>
          <revision>1-4-1</revision>
          <version_id>3</version_id>
        </version>
      </available_updates>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
      <is_top_level>true</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>group-clover-appliance</name>
      <trove_id>1</trove_id>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <version_id>1</version_id>
      </version>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%%3D/contrib.rpath.org%%40rpl%%3A2/23.0.60cvs20080523-1-0.1%%5Bdesktop%%20is%%3A%%20x86_64%%5D">
      <available_updates/>
      <flavor>desktop is: x86_64</flavor>
      <is_top_level>false</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>emacs</name>
      <trove_id>2</trove_id>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>4</version_id>
      </version>
    </trove>
  </installed_software>
"""

installed_software_xml = """\
  <installed_software>
    <trove>
      <available_updates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.13</ordering>
          <revision>1-3-1</revision>
          <version_id>2</version_id>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.14</ordering>
          <revision>1-4-1</revision>
          <version_id>3</version_id>
        </version>
      </available_updates>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
      <is_top_level>true</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>group-clover-appliance</name>
      <trove_id>1</trove_id>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <version_id>1</version_id>
      </version>
    </trove>
    <trove>
      <available_updates/>
      <flavor>desktop is: x86_64</flavor>
      <is_top_level>false</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>emacs</name>
      <trove_id>2</trove_id>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>4</version_id>
      </version>
    </trove>
  </installed_software>
"""

system_version_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/3">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/3/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/3/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/3/configuration_descriptor"/>
  %s
  <jobs id="http://testserver/api/inventory/systems/3/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <out_of_date>True</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <networks>
    <network id="http://testserver/api/inventory/networks/2">
      <active/>
      <created_date>%%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/3"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <system_events href="http://testserver/api/inventory/systems/3/system_events"/>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>%%s</created_date>
</system>
""" % get_installed_software_xml

installed_software_post_xml = """\
  <installed_software>
    <trove>
      <name>group-chater-foo-appliance</name>
      <version>
        <full>/chater-foo.eng.rpath.com@rpath:chater-foo-1-devel/1-2-1</full>
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
  </installed_software>
"""

installed_software_response_xml = """
  <installed_software>
    <trove>
      <available_updates/>
      <flavor>is: x86</flavor>
      <is_top_level>True</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>XXX</last_available_update_refresh>
      <name>group-chater-appliance</name>
      <trove_id>3</trove_id>
      <version>
        <flavor>is: x86</flavor>
        <full>/chater.eng.rpath.com@rpath:chater-1-devel/1-2-1</full>
        <label>chater.eng.rpath.com@rpath:chater-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>1-2-1</revision>
        <version_id>5</version_id>
      </version>
    </trove>
    <trove>
      <available_updates/>
      <flavor>desktop is: x86_64</flavor>
      <is_top_level>False</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>XXX</last_available_update_refresh>
      <name>vim</name>
      <trove_id>4</trove_id>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1272410163.98</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>6</version_id>
      </version>
    </trove>
  </installed_software>
"""

system_version_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <event_uuid>testeventuuid</event_uuid>
</system>
""" % installed_software_post_xml

system_version_put_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/2">
  %s
  <system_events href="http://testserver/api/inventory/systems/2/system_events"/>
  <registered>True</registered>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <managing_zone/>
  <networks>
    <network id="http://testserver/api/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/2"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <system_id>2</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/2/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <target/>
  <name/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>2010-08-23T21:41:31.278455+00:00</created_date>
</system>
""" % installed_software_response_xml

system_available_updates_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/inventory/systems/3">
  <agent_port>5989</agent_port>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/3/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/3/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/3/configuration_descriptor"/>
  <installed_software id="http://testserver/api/inventory/systems/3/installed_software">
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%3D/clover.eng.rpath.com%40rpath%3Aclover-1-devel/1-2-1%5B%7E%21dom0%2C%7E%21domU%2Cvmware%2C%7E%21xen%20is%3A%20x86%28i486%2Ci586%2Ci686%2Csse%2Csse2%29%5D">
      <name>group-clover-appliance</name>
      <trove_id>1</trove_id>
      <available_updates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567891.13</ordering>
          <revision>1-3-1</revision>
          <version_id>2</version_id>
        </version>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-4-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567892.14</ordering>
          <revision>1-4-1</revision>
          <version_id>3</version_id>
        </version>
      </available_updates>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>change me gently</revision>
        <version_id>1</version_id>
      </version>
      <last_available_update_refresh>2010-08-27T12:21:59.802463+00:00</last_available_update_refresh>
      <is_top_level>true</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>emacs</name>
      <trove_id>2</trove_id>
      <available_updates/>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>4</version_id>
      </version>
      <last_available_update_refresh>2010-08-27T12:21:59.815100+00:00</last_available_update_refresh>
      <is_top_level>false</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>desktop is: x86_64</flavor>
    </trove>
  </installed_software>
  <jobs id="http://testserver/api/inventory/systems/3/jobs">
    <completed_jobs href="http://testserver/api/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs href="http://testserver/api/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <system_events href="http://testserver/api/inventory/systems/3/system_events"/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <networks>
    <network id="http://testserver/api/inventory/networks/2">
      <active/>
      <created_date>2010-08-27T12:21:59.801387+00:00</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <required/>
      <system href="http://testserver/api/inventory/systems/3"/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
  <out_of_date>True</out_of_date>
  <registration_date/>
  <description>testsystemdescription</description>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <major_version/>
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>2010-08-27T12:21:59.800269+00:00</created_date>
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

jobs_xml = """\
<?xml version="1.0"?>
<jobs id="http://testserver/api/inventory/jobs/">
  <job id="http://testserver/api/inventory/jobs/1">
    <job_description>System registration</job_description>
    <time_updated>2010-09-16T13:36:25.939154+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>system registration</job_type>
    <time_created>2010-09-16T13:36:25.939042+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_id>1</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/inventory/jobs/2">
    <job_description>System synchronization</job_description>
    <time_updated>2010-09-16T13:36:25.943043+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>system poll</job_type>
    <time_created>2010-09-16T13:36:25.942952+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_id>2</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/inventory/jobs/3">
    <job_description>On-demand system synchronization</job_description>
    <time_updated>2010-09-16T13:36:25.946773+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>immediate system poll</job_type>
    <time_created>2010-09-16T13:36:25.946675+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid003</job_uuid>
    <job_id>3</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
</jobs>"""

job_xml = """\
<?xml version="1.0"?>
<job id="http://testserver/api/inventory/jobs/1">
  <job_description>System registration</job_description>
  <time_updated>2010-09-16T13:53:18.402208+00:00</time_updated>
  <job_state>Running</job_state>
  <job_type>system registration</job_type>
  <time_created>2010-09-16T13:53:18.402105+00:00</time_created>
  <systems/>
  <job_uuid>rmakeuuid001</job_uuid>
  <job_id>1</job_id>
  <status_code>100</status_code>
  <status_text>Initializing</status_text>
</job>"""

job_states_xml = """\
<?xml version="1.0"?>
<job_states>
  <job_state id="http://testserver/api/inventory/job_states/1">
    <job_state_id>1</job_state_id>
    <jobs href="http://testserver/api/inventory/job_states/1/jobs"/>
    <name>Queued</name>
  </job_state>
  <job_state id="http://testserver/api/inventory/job_states/2">
    <job_state_id>2</job_state_id>
    <jobs href="http://testserver/api/inventory/job_states/2/jobs"/>
    <name>Running</name>
  </job_state>
  <job_state id="http://testserver/api/inventory/job_states/3">
    <job_state_id>3</job_state_id>
    <jobs href="http://testserver/api/inventory/job_states/3/jobs"/>
    <name>Completed</name>
  </job_state>
  <job_state id="http://testserver/api/inventory/job_states/4">
    <job_state_id>4</job_state_id>
    <jobs href="http://testserver/api/inventory/job_states/4/jobs"/>
    <name>Failed</name>
  </job_state>
</job_states>"""

job_state_xml = """\
<?xml version="1.0"?>
<job_state id="http://testserver/api/inventory/job_states/1">
  <job_state_id>1</job_state_id>
  <jobs href="http://testserver/api/inventory/job_states/1/jobs"/>
  <name>Queued</name>
</job_state>"""

systems_jobs_xml = """\
<?xml version="1.0"?>
<jobs id="http://testserver/api/inventory/systems/3/jobs/">
  <job id="http://testserver/api/inventory/jobs/1">
    <job_description>System registration</job_description>
    <time_updated>2010-09-16T20:13:13.325788+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>system registration</job_type>
    <time_created>2010-09-16T20:13:13.325686+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_id>1</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/inventory/jobs/2">
    <job_description>System synchronization</job_description>
    <time_updated>2010-09-16T20:13:13.334487+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>system poll</job_type>
    <time_created>2010-09-16T20:13:13.334392+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_id>2</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/inventory/jobs/3">
    <job_description>On-demand system synchronization</job_description>
    <time_updated>2010-09-16T20:13:13.339408+00:00</time_updated>
    <job_state>Running</job_state>
    <job_type>immediate system poll</job_type>
    <time_created>2010-09-16T20:13:13.339318+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid003</job_uuid>
    <job_id>3</job_id>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
</jobs>"""


system_with_target = """\
<system id="http://testserver/api/inventory/systems/4">
  <system_events href="http://testserver/api/inventory/systems/4/system_events"/>
  <generated_uuid/>
  <networks>
    <network id="http://testserver/api/inventory/networks/3">
      <ipv6_address/>
      <network_id>3</network_id>
      <dns_name>vsphere1-002</dns_name>
      <required/>
      <system href="http://testserver/api/inventory/systems/4"/>
      <device_name/>
      <netmask/>
      <port_type/>
      <created_date>2010-09-23T13:30:14.299741+00:00</created_date>
      <active/>
      <ip_address/>
    </network>
  </networks>
  <ssl_server_certificate/>
  <stage/>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>4</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate/>
  <installed_software id="http://testserver/api/inventory/systems/4/installed_software"/>
  <out_of_date>False</out_of_date>
  <registration_date/>
  <jobs id="http://testserver/api/inventory/systems/4/jobs">
    <queued_jobs href="http://testserver/api/inventory/systems/4/job_states/1/jobs"/>
    <completed_jobs href="http://testserver/api/inventory/systems/4/job_states/3/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/4/job_states/2/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/4/job_states/4/jobs"/>
  </jobs>
  <description>vsphere1 002 description</description>
  <system_log href="http://testserver/api/inventory/systems/4/system_log"/>
  <target_system_id>vsphere1-002</target_system_id>
  <target_system_name/>
  <has_active_jobs>False</has_active_jobs>
  <has_running_jobs>False</has_running_jobs>
  <agent_port/>
  <appliance/>
  <credentials href="http://testserver/api/inventory/systems/4/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/4/configuration"/>
  <configuration_descriptor href="http://testserver/api/inventory/systems/4/configuration_descriptor"/>
  <target href="http://testserver/catalog/clouds/vmware/instances/vsphere1.eng.rpath.com">vsphere1.eng.rpath.com</target>
  <name>vsphere1 002</name>
  <local_uuid/>
  <major_version/>
  <management_interface/>
  <target_system_state/>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <current_state id="http://testserver/api/inventory/system_states/1">
    <system_state_id>1</system_state_id>
    <description>Unmanaged</description>
    <name>unmanaged</name>
    <created_date>2010-09-23T13:30:14.100890+00:00</created_date>
  </current_state>
  <created_date>2010-09-23T13:30:14.295974+00:00</created_date>
  <target_system_description/>
</system>
"""

credentials_xml = """\
<?xml version="1.0"?>
<credentials>
  <ssl_client_certificate>newsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>newsslclientkey</ssl_client_key>
</credentials>
"""

credentials_put_xml = """\
<?xml version="1.0"?>
<credentials>
  <ssl_client_certificate>updatedsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>updatedsslclientkey</ssl_client_key>
</credentials>
"""

credentials_wmi_xml = """\
<?xml version="1.0"?>
<credentials>
  <domain>testDomain</domain>
  <user>testUser</user>
  <password>testPassword</password>
</credentials>
"""

credentials_wmi_put_xml = """\
<?xml version="1.0"?>
<credentials>
  <domain>testDomainChanged</domain>
  <user>testUserChanged</user>
  <password>testPasswordChanged</password>
</credentials>
"""

credentials_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/inventory/systems/3/credentials">
  <ssl_client_certificate>newsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>newsslclientkey</ssl_client_key>
</credentials>
"""

credentials_put_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/inventory/systems/3/credentials">
  <ssl_client_certificate>updatedsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>updatedsslclientkey</ssl_client_key>
</credentials>
"""

credentials_wmi_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/inventory/systems/3/credentials">
  <domain>testDomain</domain>
  <user>testUser</user>
  <password>testPassword</password>
</credentials>
"""

credentials_wmi_put_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/inventory/systems/3/credentials">
  <domain>testDomainChanged</domain>
  <user>testUserChanged</user>
  <password>testPasswordChanged</password>
</credentials>
"""

configuration_post_xml = """\
<?xml version="1.0"?>
<configuration>
  <http_port>89</http_port>
</configuration>
"""

configuration_post_resp_xml = """\
<?xml version="1.0"?>
<configuration id="http://testserver/api/inventory/systems/3/configuration">
  <http_port>89</http_port>
</configuration>
"""

configuration_put_xml = """\
<?xml version="1.0"?>
<configuration>
  <http_port>890</http_port>
</configuration>
"""

configuration_put_resp_xml = """\
<?xml version="1.0"?>
<configuration id="http://testserver/api/inventory/systems/3/configuration">
  <http_port>890</http_port>
</configuration>
"""

configuration_descriptor_xml = """\
<configuration_descriptor><descriptor>
    <metadata>
      <displayName>Apache HTTPd Configuration</displayName>
      <descriptions>
        <desc>This is the example descriptor for configuration of httpd</desc>
      </descriptions>
    </metadata>
    <dataFields>
      <field>
        <name>org_apache_httpd_port</name>
        <descriptions>
          <desc>HTTP port number</desc>
        </descriptions>
        <prompt>
          <desc>Apache will listen for HTTP connections on this port number</desc>
        </prompt>
        <type>str</type>
        <constraints>
          <length>5</length>
        </constraints>
        <required>true</required>
      </field>
    </dataFields>
</descriptor></configuration_descriptor>"""

system_installed_software_version_stage_xml = """\
<?xml version="1.0"?>
<system id="http://testserver/api/inventory/systems/3">
  <management_interface href="http://testserver/api/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <system_events href="http://testserver/api/inventory/systems/3/system_events"/>
  <appliance href="http://testserver/api/products/chater-foo">chater-foo</appliance>
  <configuration_descriptor href="http://testserver/api/inventory/systems/3/configuration_descriptor"/>
  <has_running_jobs>True</has_running_jobs>
  <system_type href="http://testserver/api/inventory/system_types/1">Inventory</system_type>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/inventory/networks/2">
      <ipv6_address/>
      <network_id>2</network_id>
      <dns_name>testnetwork.example.com</dns_name>
      <required/>
      <system href="http://testserver/api/inventory/systems/3"/>
      <device_name>eth0</device_name>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <created_date>2010-11-10T22:52:26.350321+00:00</created_date>
      <active/>
      <ip_address>1.1.1.1</ip_address>
    </network>
  </networks>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <managing_zone href="http://testserver/api/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <installed_software id="http://testserver/api/inventory/systems/3/installed_software">
    <trove id="http://testserver/repos/chater-foo/api/trove/group-chater-foo-appliance%3D/chater-foo.eng.rpath.com%40rpath%3Achater-foo-1-devel/1-2-1%5Bis%3A%20x86%5D">
      <name>group-chater-foo-appliance</name>
      <is_top_level_item>True</is_top_level_item>
      <trove_id>3</trove_id>
      <available_updates/>
      <version>
        <flavor>is: x86</flavor>
        <full>/chater-foo.eng.rpath.com@rpath:chater-foo-1-devel/1-2-1</full>
        <label>chater-foo.eng.rpath.com@rpath:chater-foo-1-devel</label>
        <ordering>1234567890.12</ordering>
        <revision>1-2-1</revision>
        <version_id>5</version_id>
      </version>
      <last_available_update_refresh/>
      <is_top_level>true</is_top_level>
      <flavor>is: x86</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/vim%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>vim</name>
      <is_top_level_item>True</is_top_level_item>
      <trove_id>4</trove_id>
      <available_updates/>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1272410163.98</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>6</version_id>
      </version>
      <last_available_update_refresh/>
      <is_top_level>false</is_top_level>
      <flavor>desktop is: x86_64</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/info-sfcb%3D/contrib.rpath.org%40rpl%3A2/1-1-1%5B%5D">
      <name>info-sfcb</name>
      <is_top_level_item>True</is_top_level_item>
      <trove_id>5</trove_id>
      <available_updates/>
      <version>
        <flavor/>
        <full>/contrib.rpath.org@rpl:2/1-1-1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1263856871.03</ordering>
        <revision>1-1-1</revision>
        <version_id>7</version_id>
      </version>
      <last_available_update_refresh/>
      <is_top_level>false</is_top_level>
      <flavor/>
    </trove>
  </installed_software>
  <target_system_id/>
  <jobs id="http://testserver/api/inventory/systems/3/jobs">
    <queued_jobs href="http://testserver/api/inventory/systems/3/job_states/1/jobs"/>
    <completed_jobs href="http://testserver/api/inventory/systems/3/job_states/3/jobs"/>
    <running_jobs href="http://testserver/api/inventory/systems/3/job_states/2/jobs"/>
    <failed_jobs href="http://testserver/api/inventory/systems/3/job_states/4/jobs"/>
  </jobs>
  <description>testsystemdescription</description>
  <system_log href="http://testserver/api/inventory/systems/3/system_log"/>
  <registration_date/>
  <has_active_jobs>True</has_active_jobs>
  <target_system_name/>
  <credentials href="http://testserver/api/inventory/systems/3/credentials"/>
  <configuration href="http://testserver/api/inventory/systems/3/configuration"/>
  <agent_port>5989</agent_port>
  <stage href="http://testserver/api/products/chater-foo/versions/1/stages/Development">Development</stage>
  <out_of_date>False</out_of_date>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <target_system_state/>
  <major_version href="http://testserver/api/products/chater-foo/versions/1">1</major_version>
  <current_state id="http://testserver/api/inventory/system_states/2">
    <system_state_id>2</system_state_id>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <created_date>2010-11-10T22:52:26.167013+00:00</created_date>
  </current_state>
  <target/>
  <target_system_description/>
  <created_date>2010-11-10T22:52:26.343993+00:00</created_date>
</system>"""
