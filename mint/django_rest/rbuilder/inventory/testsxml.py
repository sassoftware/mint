#!/usr/bin/python 
inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <event_types id="http://testserver/api/v1/inventory/event_types"/>
  <image_import_metadata_descriptor id="http://testserver/api/v1/inventory/image_import_metadata_descriptor"/>
  <infrastructure_systems id="http://testserver/api/v1/inventory/infrastructure_systems"/>
  <inventory_systems id="http://testserver/api/v1/inventory/inventory_systems"/>
  <job_states id="http://testserver/api/v1/inventory/job_states"/>
  <log id="http://testserver/api/v1/inventory/log"/>
  <zones id="http://testserver/api/v1/inventory/zones"/>
  <management_nodes id="http://testserver/api/v1/inventory/management_nodes"/>
  <management_interfaces id="http://testserver/api/v1/inventory/management_interfaces"/>
  <system_types id="http://testserver/api/v1/inventory/system_types"/>
  <systems id="http://testserver/api/v1/inventory/systems"/>
  <system_states id="http://testserver/api/v1/inventory/system_states"/>
  <networks id="http://testserver/api/v1/inventory/networks"/>
</inventory>"""

event_type_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/v1/inventory/event_types/1">
  <description>System registration</description>
  <priority>70</priority>
  <resource_type>System</resource_type>
  <job_type_id>1</job_type_id>
  <name>system registration</name>
  <system_events/>
</event_type>"""

event_types_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_types>
  <event_type id="http://testserver/api/v1/inventory/event_types/1">
    <name>system registration</name>
    <priority>70</priority>
    <job_type_id>1</job_type_id>
    <resource_type>System</resource_type>
    <description>System registration</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/2">
    <name>system poll</name>
    <priority>50</priority>
    <job_type_id>2</job_type_id>
    <resource_type>System</resource_type>
    <description>System synchronization</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/3">
    <name>immediate system poll</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <job_type_id>3</job_type_id>
    <description>On-demand system synchronization</description>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/4">
    <description>Scheduled system update</description>
    <job_type_id>4</job_type_id>
    <name>system apply update</name>
    <resource_type>System</resource_type>
    <priority>50</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/5">
    <description>System update</description>
    <job_type_id>5</job_type_id>
    <resource_type>System</resource_type>
    <name>immediate system apply update</name>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/6">
    <description>Scheduled system shutdown</description>
    <job_type_id>6</job_type_id>
    <name>system shutdown</name>
    <priority>50</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/7">
    <description>System shutdown</description>
    <job_type_id>7</job_type_id>
    <name>immediate system shutdown</name>
    <resource_type>System</resource_type>
    <priority>105</priority>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/8">
    <description>Launched system network data discovery</description>
    <job_type_id>8</job_type_id>
    <name>system launch wait</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/9">
    <description>System management interface detection</description>
    <job_type_id>9</job_type_id>
    <name>system detect management interface</name>
    <priority>50</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/10">
    <description>On-demand system management interface detection</description>
    <job_type_id>10</job_type_id>
    <name>immediate system detect management interface</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/11">
    <description>Update system configuration</description>
    <job_type_id>11</job_type_id>
    <name>immediate system configuration</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/12">
    <description>System assimilation</description>
    <job_type_id>12</job_type_id>
    <name>system assimilation</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/13">
    <description>Image builds</description>
    <job_type_id>13</job_type_id>
    <name>image builds</name>
    <priority>105</priority>
    <resource_type>Image</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/14">
    <description>Refresh queryset</description>
    <job_type_id>14</job_type_id>
    <name>refresh queryset</name>
    <priority>105</priority>
    <resource_type>QuerySet</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/15">
    <description>Refresh target images</description>
    <job_type_id>15</job_type_id>
    <name>refresh target images</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/16">
    <description>Refresh target systems</description>
    <job_type_id>16</job_type_id>
    <name>refresh target systems</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/17">
    <description>Deploy image on target</description>
    <job_type_id>17</job_type_id>
    <name>deploy image on target</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/18">
    <description>Launch system on target</description>
    <job_type_id>18</job_type_id>
    <name>launch system on target</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/19">
    <description>Create target</description>
    <job_type_id>19</job_type_id>
    <name>create target</name>
    <priority>105</priority>
    <resource_type>TargetType</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/20">
    <description>Configure target credentials for the current user</description>
    <job_type_id>20</job_type_id>
    <name>configure target credentials</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/21">
    <description>Capture a system's image</description>
    <job_type_id>21</job_type_id>
    <name>system capture</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/22">
    <description>Configure target</description>
    <job_type_id>22</job_type_id>
    <name>configure target</name>
    <priority>105</priority>
    <resource_type>TargetType</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/23">
    <description>On-demand system registration</description>
    <job_type_id>23</job_type_id>
    <name>immediate system registration</name>
    <priority>110</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/24">
    <description>Scan system</description>
    <job_type_id>24</job_type_id>
    <name>system scan</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/25">
    <description>Cancel an image build</description>
    <job_type_id>25</job_type_id>
    <name>image build cancellation</name>
    <priority>105</priority>
    <resource_type>Image</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/26">
    <description>Update your system</description>
    <job_type_id>26</job_type_id>
    <name>system update software</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
  <event_type id="http://testserver/api/v1/inventory/event_types/27">
    <description>Apply system configuration</description>
    <job_type_id>27</job_type_id>
    <name>system apply configuration</name>
    <priority>105</priority>
    <resource_type>System</resource_type>
    <system_events/>
  </event_type>
</event_types>"""

event_type_put_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/v1/inventory/event_types/%(event_type_id)s">
  <description>System registration</description>
  <priority>1</priority>
  <event_type_id>%(event_type_id)s</event_type_id>
  <name>system registration</name>
  <system_events/>
</event_type>"""

event_type_put_name_change_xml="""\
<?xml version="1.0" encoding="UTF-8"?>
<event_type id="http://testserver/api/v1/inventory/event_types/%(event_type_id)s">
  <description>System registration</description>
  <priority>110</priority>
  <event_type_id>%(event_type_id)s</event_type_id>
  <name>foobar</name>
  <system_events/>
</event_type>"""

zones_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zones>
  <zone id="http://testserver/api/v1/inventory/zones/2">
    <description>Some local zone</description>
    <created_date>%s</created_date>
    <name>Local Zone</name>
    <management_nodes/>
    <zone_id>2</zone_id>
   </zone>
</zones>
"""

zone_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<zone id="http://testserver/api/v1/inventory/zones/2">
  <description>Some local zone</description>
  <created_date>%s</created_date>
  <name>Local Zone</name>
  <management_nodes/>
  <zone_id>2</zone_id>
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
<zone id="http://testserver/api/v1/inventory/zones/2">
  <description>Some local zone</description>
  <created_date>%s</created_date>
  <name>Local Zone</name>
  <management_nodes/>
  <zone_id>2</zone_id>
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
<zone id="http://testserver/api/v1/inventory/zones/2">
  <description>zoneputdesc</description>
  <name>zoneputname</name>
  <created_date>%s</created_date>
</zone>
"""

management_interfaces_xml="""\
<?xml version="1.0"?>
<management_interfaces>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/4">
    <description>bar</description>
    <management_interface_id>4</management_interface_id>
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
<management_interface id="http://testserver/api/v1/inventory/management_interfaces/4">
  <description>bar</description>
  <management_interface_id>4</management_interface_id>
  <created_date>2010-10-06T00:11:27.828160+00:00</created_date>
  <credentials_descriptor><foo/></credentials_descriptor>
  <port>8000</port>
  <name>foo</name>
  <credentials_readonly/>
</management_interface>
"""

management_interface_put_xml="""\
<?xml version="1.0"?>
<management_interface id="http://testserver/api/v1/inventory/management_interfaces/4/">
  <systems/>
  <description>bar</description>
  <management_interface_id>4</management_interface_id>
  <created_date>2010-10-06T00:11:27.828160+00:00</created_date>
  <credentials_descriptor><foo/></credentials_descriptor>
  <port>123</port>
  <name>thisnameshouldnotstick</name>
</management_interface>
"""

system_types_xml="""\
<?xml version="1.0"?>
<system_types>
  <system_type id="http://testserver/api/v1/inventory/system_types/4">
    <system_type_id>4</system_type_id>
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
<system_type id="http://testserver/api/v1/inventory/system_types/4">
  <system_type_id>4</system_type_id>
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
<system_type id="http://testserver/api/v1/inventory/system_types/1">
  <system_type_id>1</system_type_id>
  <infrastructure>true</infrastructure>
  <description>bar</description>
  <name>thisnameshouldnotstick</name>
  <created_date>2010-10-07T00:42:33.634913+00:00</created_date>
</system_type>"""

system_type_systems_xml="""
<?xml version="1.0"?>
<systems count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/inventory/systems" id="http://testserver/api/v1/inventory/systems;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <system id="http://testserver/api/v1/inventory/systems/3">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
    <source_image/>
    <agent_port>5989</agent_port>
    <project/>
    <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
    <current_state id="http://testserver/api/v1/inventory/system_states/3">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <desired_top_level_items/>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
      <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
      <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <project_branch/>
    <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <network_address>
      <address>1.1.1.1</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/2">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <pinned/>
      </network>
    </networks>
    <observed_top_level_items/>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <project_branch_stage/>
    <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
    <system_id>3</system_id>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
    <target/>
    <target_system_description/>
    <target_system_id/>
    <target_system_name/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  </system>
</systems>
"""

networks_xml = """\
<?xml version="1.0"?>
<networks>
  <systems id="http://testserver/api/v1/inventory/systems"/>
  <network id="http://testserver/api/v1/inventory/networks/2">
    <active/>
    <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
    <device_name>eth0</device_name>
    <dns_name>testnetwork.example.com</dns_name>
    <ip_address>1.1.1.1</ip_address>
    <ipv6_address/>
    <netmask>255.255.255.0</netmask>
    <network_id>2</network_id>
    <port_type>lan</port_type>
    <system id="http://testserver/api/v1/inventory/systems/3"/>
    <pinned/>
  </network>
</networks>"""

network_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/v1/inventory/networks/2">
  <active/>
  <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
  <device_name>eth0</device_name>
  <dns_name>testnetwork.example.com</dns_name>
  <ip_address>1.1.1.1</ip_address>
  <ipv6_address/>
  <netmask>255.255.255.0</netmask>
  <network_id>2</network_id>
  <port_type>lan</port_type>
  <system id="http://testserver/api/v1/inventory/systems/3"/>
  <pinned/>
</network>"""

network_put_xml = """\
<?xml version="1.0"?>
<network id="http://testserver/api/v1/inventory/networks/2">
  <active/>
  <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
  <device_name>eth0</device_name>
  <dns_name>new.com</dns_name>
  <ip_address>2.2.2.2</ip_address>
  <ipv6_address/>
  <netmask>255.255.255.0</netmask>
  <network_id>2</network_id>
  <port_type>lan</port_type>
  <system id="http://testserver/api/v1/inventory/systems/3"/>
  <pinned/>
</network>"""

network_put_xml_opt_ip_addr = """\
<?xml version="1.0"?>
<network id="http://testserver/api/v1/inventory/networks/1">
  <active/>
  <created_date>2010-09-15T21:41:40.142078+00:00</created_date>
  <device_name>eth0</device_name>
  <dns_name>new.com</dns_name>
  <ip_address>%s</ip_address>
  <ipv6_address/>
  <netmask>255.255.255.0</netmask>
  <network_id>2</network_id>
  <port_type>lan</port_type>
  <system id="http://testserver/api/v1/inventory/systems/3"/>
  <pinned/>
</network>"""

system_states_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_states>
  <system_state id="http://testserver/api/v1/inventory/system_states/1">
    <system_state_id>1</system_state_id>
    <description>Unmanaged</description>
    <name>unmanaged</name>
    <created_date>2010-09-03T18:23:42.656549+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/2">
    <system_state_id>2</system_state_id>
    <description>Unmanaged: Invalid credentials</description>
    <name>unmanaged-credentials</name>
    <created_date>2010-09-03T18:23:42.658249+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/3">
    <system_state_id>3</system_state_id>
    <description>Registered</description>
    <name>registered</name>
    <created_date>2010-09-03T18:23:42.659883+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/4">
    <system_state_id>4</system_state_id>
    <description>Online</description>
    <name>responsive</name>
    <created_date>2010-09-03T18:23:42.661629+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/5">
    <system_state_id>5</system_state_id>
    <description>Not responding: Unknown</description>
    <name>non-responsive-unknown</name>
    <created_date>2010-09-03T18:23:42.663290+00:00</created_date>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/6">
    <system_state_id>6</system_state_id>
    <description>Not responding: Network unreachable</description>
    <name>non-responsive-net</name>
    <created_date>2010-09-03T18:23:42.664943+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/v1/inventory/system_states/7">
      <system_state_id>7</system_state_id>
      <description>Not responding: Host unreachable</description>
      <name>non-responsive-host</name>
      <created_date>2010-09-03T18:23:42.666612+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/v1/inventory/system_states/8">
      <system_state_id>8</system_state_id>
      <description>Not responding: Shutdown</description>
      <name>non-responsive-shutdown</name>
      <created_date>2010-09-03T18:23:42.668266+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/v1/inventory/system_states/9">
      <system_state_id>9</system_state_id>
      <description>Not responding: Suspended</description>
      <name>non-responsive-suspended</name>
      <created_date>2010-09-03T18:23:42.669899+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/v1/inventory/system_states/10">
      <system_state_id>10</system_state_id>
      <description>Not responding: Invalid credentials</description>
      <name>non-responsive-credentials</name>
      <created_date>2010-09-03T18:23:42.671647+00:00</created_date>
    </system_state>
    <system_state id="http://testserver/api/v1/inventory/system_states/11">
    <description>Stale</description>
    <name>dead</name>
    <system_state_id>11</system_state_id>
  </system_state>
  <system_state id="http://testserver/api/v1/inventory/system_states/12">
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>12</system_state_id>
  </system_state>
</system_states>"""

system_state_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_state id="http://testserver/api/v1/inventory/system_states/1">
  <system_state_id>1</system_state_id>
  <description>Unmanaged</description>
  <name>unmanaged</name>
  <created_date>2010-09-03T18:23:42.656549+00:00</created_date>
</system_state>"""

management_nodes_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_nodes>
  <management_node id="http://testserver/api/v1/inventory/management_nodes/3">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/management_nodes/3/surveys"/>
    <agent_port>5989</agent_port>
    <project/>
    <credentials id="http://testserver/api/v1/inventory/management_nodes/3/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/management_nodes/3/configuration"/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/management_nodes/3/configuration_descriptor"/>
    <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <generated_uuid>test management node guuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <network_address>
      <address>2.2.2.2</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/2">
        <active/>
        <created_date>%s</created_date>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>2.2.2.2</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <pinned/>
      </network>
    </networks>
    <node_jid>superduperjid2@rbuilder.rpath</node_jid>
    <ssl_client_certificate>test management node client cert</ssl_client_certificate>
    <ssl_server_certificate>test management node server cert</ssl_server_certificate>
    <project_branch_stage/>
    <managing_zone id="http://testserver/api/v1/inventory/zones/2">Local Zone</managing_zone>
    <hostname/>
    <name>test management node</name>
    <system_id>3</system_id>
    <launching_user/>
    <launch_date/>
    <local>true</local>
    <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
      <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
      <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
    </jobs>
    <description>test management node desc</description>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
    <target/>
    <zone id="http://testserver/api/v1/inventory/zones/2"/>
    <system_ptr id="http://testserver/api/v1/inventory/systems/3"/>
    <local_uuid>test management node luuid</local_uuid>
    <project_branch/>
    <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/v1/inventory/system_states/3">
      <created_date>%s</created_date>
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <created_date>%s</created_date>
    <source_image/>
  </management_node>
</management_nodes>
"""

management_node_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/v1/inventory/management_nodes/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/management_nodes/3/surveys"/>
  <agent_port>5989</agent_port> 
  <project/>
  <credentials id="http://testserver/api/v1/inventory/management_nodes/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/management_nodes/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/management_nodes/3/configuration_descriptor"/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <node_jid>superduperjid2@rbuilder.rpath</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/2">Local Zone</managing_zone>
  <hostname/>
  <name>test management node</name>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <description>test management node desc</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <zone id="http://testserver/api/v1/inventory/zones/2"/>
  <system_ptr id="http://testserver/api/v1/inventory/systems/3"/>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <created_date>%s</created_date>
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</management_node>"""

management_node_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node>
  <ssl_client_key>test management node client key</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <networks>
    <network>
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <project_branch_stage/>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1"/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>true</local>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <description>test management node desc</description>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
</management_node>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/v1/inventory/management_nodes/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/management_nodes/3/surveys"/>
  <agent_port>5989</agent_port> 
  <project/>
  <credentials id="http://testserver/api/v1/inventory/management_nodes/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/management_nodes/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/management_nodes/3/configuration_descriptor"/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate/>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <description>test management node desc</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <system_ptr id="http://testserver/api/v1/inventory/systems/3"/>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <created_date>%s</created_date>
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</management_node>"""

management_node_zone_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node>
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <ssl_client_key>test management node client key</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <networks>
    <network>
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <project_branch_stage/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>true</local>
  <ssl_client_certificate>test management node client cert</ssl_client_certificate>
  <description>test management node desc</description>
  <zone id="http://testserver/api/v1/inventory/zones/2"/>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1"/>
</management_node>"""

management_node_zone_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/v1/inventory/management_nodes/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/management_nodes/3/surveys"/>
  <agent_port>5989</agent_port>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/management_nodes/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/management_nodes/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/management_nodes/3/configuration_descriptor"/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/1">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>2.2.2.2</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <node_jid>abcd</node_jid>
  <ssl_client_certificate/>
  <ssl_server_certificate>test management node server cert</ssl_server_certificate>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <local>true</local>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <description>test management node desc</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
  <target/>
  <zone id="http://testserver/api/v1/inventory/zones/2"/>
  <system_ptr id="http://testserver/api/v1/inventory/systems/3"/>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <created_date>%s</created_date>
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</management_node>"""

# note that top level <systems> tag is going to be different now that we
# are redirecting collections to query sets.  the <systems> tag's id and
# collection parameters have been modified to match the expected value
# generated by _get (the one which redirects) in the testsuite

systems_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/query_sets/5/all" id="http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <system id="http://testserver/api/v1/inventory/systems/2">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/2/surveys"/>
    <actions>
      <action>
        <description>Assimilate system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/2/descriptors/assimilation"/>
        <enabled>false</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
        <key>system_assimilation</key>
        <name>Assimilate system</name>
      </action>
      <action>
        <description>Scan system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/2/descriptors/survey_scan"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/24"/>
        <key>system_scan</key>
        <name>System scan</name>
      </action>
      <action>
        <description>Capture a system's image</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/2/descriptors/capture"/>
        <enabled>false</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
        <key>system_capture</key>
        <name>System capture</name>
      </action>
      <action>
        <description>Update your system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/2/descriptors/update"/>
        <enabled>True</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/26"/>
        <key>system_update_software</key>
        <name>Update Software</name>
      </action>
      <action>
        <description>Apply system configuration</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/2/descriptors/configure"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
        <key>system_apply_configuration</key>
        <name>Apply system configuration</name>
     </action>
    </actions>
    <agent_port/>
    <project/>
    <credentials id="http://testserver/api/v1/inventory/systems/2/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/2/configuration"/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/2/configuration_descriptor"/>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <created_date>2010-08-18T22:28:26+00:00</created_date>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <system_state_id>1</system_state_id>
    </current_state>
    <description>Local rPath Update Service</description>
    <desired_top_level_items/>
    <observed_top_level_items/>
    <generated_uuid/>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <jobs id="http://testserver/api/v1/inventory/systems/2/jobs">
      <completed_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/3/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/4/jobs"/>
      <queued_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/1/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid/>
    <project_branch/>
    <management_interface/>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>rPath Update Service</name>
    <network_address>
      <address>127.0.0.1</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/1">
        <active/>
        <created_date>2010-08-18T22:28:26+00:00</created_date>
        <device_name/>
        <dns_name>127.0.0.1</dns_name>
        <ip_address/>
        <ipv6_address/>
        <netmask/>
        <network_id>1</network_id>
        <port_type/>
        <system id="http://testserver/api/v1/inventory/systems/2"/>
        <pinned/>
      </network>
    </networks>
    <ssl_client_certificate/>
    <ssl_server_certificate/>
    <project_branch_stage/>
    <system_events id="http://testserver/api/v1/inventory/systems/2/system_events"/>
    <system_id>2</system_id>
    <system_log id="http://testserver/api/v1/inventory/systems/2/system_log"/>
    <target/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/3">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
    <actions>
      <action>
        <description>Assimilate system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/assimilation"/>
        <enabled>false</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
        <key>system_assimilation</key>
        <name>Assimilate system</name>
      </action>
      <action>
        <description>Scan system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/survey_scan"/>
        <enabled>True</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/24"/>
        <key>system_scan</key>
        <name>System scan</name>
      </action>
      <action>
        <description>Capture a system's image</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/capture"/>
        <enabled>false</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
        <key>system_capture</key>
        <name>System capture</name>
      </action>
      <action>
        <description>Update your system</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/update"/>
        <enabled>True</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/26"/>
        <key>system_update_software</key>
        <name>Update Software</name>
      </action>
      <action>
        <description>Apply system configuration</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/configure"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
        <key>system_apply_configuration</key>
        <name>Apply system configuration</name>
     </action>
    </actions>
    <agent_port>5989</agent_port>
    <project/>
    <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <created_date>%s</created_date>
    <current_state id="http://testserver/api/v1/inventory/system_states/3">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <desired_top_level_items/>
    <observed_top_level_items/>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
      <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
      <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
    </jobs>
    <launch_date/>
    <launching_user/>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <project_branch/>
    <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <network_address>
      <address>1.1.1.1</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/2">
        <active/>
        <created_date>%s</created_date>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <pinned/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <project_branch_stage/>
    <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
    <system_id>3</system_id>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
    <target/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <source_image/>
  </system>
</systems>
"""

systems_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems>
  <system id="http://testserver/api/v1/inventory/systems/1">
    <surveys id="http://testserver/api/v1/inventory/systems/1/surveys"/>
    <ssl_client_key>testsystemsslclientkey</ssl_client_key>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/1">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork.example.com</dns_name>
        <ip_address>1.1.1.1</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>1</network_id>
        <port_type>lan</port_type>
        <pinned/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <project_branch_stage/>
    <launch_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <description>testsystemdescription</description>
    <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <system_events id="http://testserver/api/v1/inventory/systems/1/system_events"/>
    <name>testsystemname</name>
    <local_uuid>testsystemlocaluuid</local_uuid>
    <project_branch/>
    <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/v1/inventory/system_states/2">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/2">
    <surveys id="http://testserver/api/v1/inventory/systems/2/surveys"/>
    <ssl_client_key>testsystemsslclientkey</ssl_client_key>
    <out_of_date>false</out_of_date>
    <registration_date/>
    <generated_uuid>testsystem2generateduuid</generated_uuid>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/1">
        <active/>
        <device_name>eth0</device_name>
        <dns_name>testnetwork2.example.com</dns_name>
        <ip_address>2.2.2.2</ip_address>
        <ipv6_address/>
        <netmask>255.255.255.0</netmask>
        <network_id>2</network_id>
        <port_type>lan</port_type>
        <pinned/>
      </network>
    </networks>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
    <project_branch_stage/>
    <launch_date/>
    <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
    <description>testsystemdescription</description>
    <system_log id="http://testserver/api/v1/inventory/systems/2/system_log"/>
    <target_system_id/>
    <target_system_name/>
    <target_system_description/>
    <target_system_state/>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <system_events id="http://testserver/api/v1/inventory/systems/2/system_events"/>
    <name>testsystemname</name>
    <local_uuid>testsystem2localuuid</local_uuid>
    <project_branch/>
    <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
    <current_state id="http://testserver/api/v1/inventory/system_states/2">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
    <source_image/>
  </system>
</systems>"""

systems_put_mothball_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_events id="http://testserver/api/v1/inventory/systems/1/system_events"/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/12">
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>12</system_state_id>
  </current_state>
  <source_image/>
</system>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <actions>
    <action>
      <description>Assimilate system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/assimilation"/>
      <enabled>false</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
      <key>system_assimilation</key>
      <name>Assimilate system</name>
    </action>
    <action>
      <description>Scan system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/survey_scan"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/24"/>
      <key>system_scan</key>
      <name>System scan</name>
    </action>
    <action>
      <description>Capture a system's image</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/capture"/>
      <enabled>false</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
      <key>system_capture</key>
      <name>System capture</name>
    </action>
    <action>
      <description>Update your system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/update"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/26"/>
      <key>system_update_software</key>
      <name>Update Software</name>
    </action>
    <action>
        <description>Apply system configuration</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/configure"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
        <key>system_apply_configuration</key>
        <name>Apply system configuration</name>
     </action>
  </actions>
  <agent_port>5989</agent_port>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <desired_top_level_items/>
  <observed_top_level_items/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</system>"""

system_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network>
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <source_image/>
</system>"""

system_post_xml_bad_network = """
<system>
    <configuration />
    <current_state />
    <description>exampleNewDescription</description>
    <management_interface />
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>exampleNewSystem</name>
    <network_address>
        <address>user@notanemail.address.rpath.com</address>
        <pinned>true</pinned>
    </network_address>
    <networks />
    <refresh_delay>0</refresh_delay>
    <should_migrate>false</should_migrate>
    <system_tags />
    <system_type id="https://dhcp244.eng.rpath.com/api/v1/inventory/system_types/1" href="https://dhcp244.eng.rpath.com/api/v1/inventory/system_types/1" />
</system>
"""


system_mgmt_interface_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/2">Windows Management Instrumentation (WMI)</management_interface>
  <source_image/>
</system>"""

system_delete_mgmt_interface_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface/>
  <source_image/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <agent_port>5989</agent_port>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <description>testsystemdescription</description>
  <desired_top_level_items/>
  <observed_top_level_items/>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <target/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/4">
    <description>Online</description>
    <name>responsive</name>
    <system_state_id>4</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</system>"""

system_post_no_network_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <name>testsystemname</name>
  <description>testsystemlocaluuid</description>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
</system>"""

system_post_network_unpinned = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <name>testsystemname</name>
  <description>testsystemlocaluuid</description>
  <managing_zone href="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <network_address>
    <address>1.2.3.4</address>
    <pinned>false</pinned>
  </network_address>
  <source_image/>
</system>"""

system_post_network_pinned = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <name>testsystemname</name>
  <description>testsystemlocaluuid</description>
  <managing_zone href="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <network_address>
    <address>1.2.3.4</address>
    <pinned>true</pinned>
  </network_address>
  <source_image/>
</system>"""

system_post_xml_dup = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network>
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <source_image/>
</system>"""

system_post_xml_dup2 = system_post_xml_dup.replace(
    '<name>testsystemname</name>', 
    '<name>testsystemnameChanged</name>')

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <actions>
    <action>
      <description>Assimilate system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/assimilation"/>
      <enabled>false</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
      <key>system_assimilation</key>
      <name>Assimilate system</name>
    </action>
    <action>
      <description>Scan system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/survey_scan"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/24"/>
      <key>system_scan</key>
      <name>System scan</name>
    </action>
    <action>
      <description>Capture a system's image</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/capture"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
      <key>system_capture</key>
      <name>System capture</name>
   </action>
    <action>
      <description>Update your system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/update"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/26"/>
      <key>system_update_software</key>
      <name>Update Software</name>
    </action>
   <action>
      <description>Apply system configuration</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/configure"/>
      <enabled>False</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
      <key>system_apply_configuration</key>
      <name>Apply system configuration</name>
   </action>
  </actions>
  <agent_port>5989</agent_port>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  <desired_top_level_items/>
  <observed_top_level_items/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
   </jobs>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <name>testsystemname</name>
  <target id="http://testserver/api/v1/targets/4">testtargetname</target>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%s</created_date>
  <source_image/>
</system>
"""

system_events_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_events>
    <system_event id="http://testserver/api/v1/inventory/system_events/1">
        <event_data/>
        <event_type id="http://testserver/api/v1/inventory/event_types/2"/>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <time_created>%s</time_created>
        <priority>50</priority>
        <time_enabled>%s</time_enabled>
        <system_event_id>1</system_event_id>
    </system_event>
    <system_event id="http://testserver/api/v1/inventory/system_events/2">
        <event_data/>
        <event_type id="http://testserver/api/v1/inventory/event_types/1"/>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <time_created>%s</time_created>
        <priority>70</priority>
        <time_enabled>%s</time_enabled>
        <system_event_id>2</system_event_id>
    </system_event>
</system_events>
"""

system_event_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event id="http://testserver/api/v1/inventory/system_events/1">
    <event_data/>
    <event_type id="http://testserver/api/v1/inventory/event_types/26"/>
    <system id="http://testserver/api/v1/inventory/systems/3"/>
    <time_created>%s</time_created>
    <priority>105</priority>
    <time_enabled>%s</time_enabled>
    <system_event_id>1</system_event_id>
</system_event>
"""

system_event_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type id="http://testserver/api/v1/inventory/event_types/26"/>
    <system id="http://testserver/api/v1/inventory/systems/26"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_poll_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type id="http://testserver/api/v1/inventory/event_types/3"/>
    <system id="http://testserver/api/v1/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_update_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type id="http://testserver/api/v1/inventory/event_types/26"/>
    <system id="http://testserver/api/v1/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_shutdown_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type id="http://testserver/api/v1/inventory/event_types/7"/>
    <system id="http://testserver/api/v1/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_event_immediate_registration_post_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_event>
    <event_type id="http://testserver/api/v1/inventory/event_types/23"/>
    <system id="http://testserver/api/v1/inventory/systems/2"/>
    <priority>50</priority>
</system_event>
"""

system_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system_log id="http://testserver/api/v1/inventory/systems/3/system_log">
  <system_log_entries>
    <system_log_entry>
      <entry>System added to inventory</entry>
      <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
      <system_log_entry_id>1</system_log_entry_id>
    </system_log_entry>
    <system_log_entry>
      <entry>System registered via rpath-tools</entry>
      <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
      <system_log_entry_id>2</system_log_entry_id>
    </system_log_entry>
  </system_log_entries>
  <system_log_id>1</system_log_id>
  <system id="http://testserver/api/v1/inventory/systems/3"/>
</system_log>
"""

systems_log_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<systems_log>
  <system_log_entry>
    <entry>System added to inventory</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
    <system_log_entry_id>1</system_log_entry_id>
  </system_log_entry>
   <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
     <system_log_entry_id>2</system_log_entry_id>
   </system_log_entry>
   <system_log_entry>
     <entry>System added to inventory</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/4/system_log"/>
     <system_log_entry_id>3</system_log_entry_id>
   </system_log_entry>
  <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/4/system_log"/>
    <system_log_entry_id>4</system_log_entry_id>
  </system_log_entry>
  <system_log_entry>
    <entry>System added to inventory</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/5/system_log"/>
    <system_log_entry_id>5</system_log_entry_id>
  </system_log_entry>
  <system_log_entry>
    <entry>Unable to create event 'On-demand system management interface detection': no networking information</entry>
    <system_log id="http://testserver/api/v1/inventory/systems/5/system_log"/>
    <system_log_entry_id>6</system_log_entry_id>
  </system_log_entry>
</systems_log>
"""

system_version_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <agent_port>5989</agent_port>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  %s
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <out_of_date>true</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>%%s</created_date>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>2</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%%s</created_date>
  <source_image/>
</system>
"""

system_version_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  %s
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <event_uuid>testeventuuid</event_uuid>
</system>
"""

system_version_put_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/2">
  %s
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set >
  <surveys id="http://testserver/api/v1/inventory/systems/2/surveys"/>
  <system_events id="http://testserver/api/v1/inventory/systems/2/system_events"/>
  <registered>True</registered>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <managing_zone/>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/1">
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <network_id>1</network_id>
      <port_type>lan</port_type>
      <system id="http://testserver/api/v1/inventory/systems/2"/>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <system_id>2</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/2/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <target/>
  <name/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/2">
    <description>Registered</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>2010-08-23T21:41:31.278455+00:00</created_date>
  <source_image/>
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

system_with_target = """\
<system id="http://testserver/api/v1/inventory/systems/4">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/4/surveys"/>
  <actions>
    <action>
      <description>Assimilate system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/4/descriptors/assimilation"/>
      <enabled>false</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
      <key>system_assimilation</key>
      <name>Assimilate system</name>
    </action>
    <action>
      <description>Scan system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/4/descriptors/survey_scan"/>
      <enabled>False</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/24"/>
      <key>system_scan</key>
      <name>System scan</name>
    </action>
    <action>
      <description>Capture a system's image</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/4/descriptors/capture"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
      <key>system_capture</key>
      <name>System capture</name>
    </action>
    <action>
      <description>Update your system</description>
      <descriptor id="http://testserver/api/v1/inventory/systems/4/descriptors/update"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/26"/>
      <key>system_update_software</key>
      <name>Update Software</name>
    </action>
    <action>
        <description>Apply system configuration</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/4/descriptors/configure"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
        <key>system_apply_configuration</key>
        <name>Apply system configuration</name>
     </action>
  </actions>
  <system_events id="http://testserver/api/v1/inventory/systems/4/system_events"/>
  <generated_uuid/>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/3">
      <ipv6_address/>
      <network_id>3</network_id>
      <dns_name>vsphere1-002</dns_name>
      <system id="http://testserver/api/v1/inventory/systems/4"/>
      <pinned/>
      <device_name/>
      <netmask/>
      <port_type/>
      <created_date>2010-09-23T13:30:14.299741+00:00</created_date>
      <active/>
      <ip_address/>
    </network>
  </networks>
  <ssl_server_certificate/>
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>4</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate/>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <jobs id="http://testserver/api/v1/inventory/systems/4/jobs">
    <queued_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/1/jobs"/>
    <completed_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/3/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/2/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/4/jobs"/>
  </jobs>
  <description>vsphere1 002 description</description>
  <system_log id="http://testserver/api/v1/inventory/systems/4/system_log"/>
  <target_system_id>vsphere1-002</target_system_id>
  <target_system_name/>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <agent_port/>
  <project/>
  <credentials id="http://testserver/api/v1/inventory/systems/4/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/4/configuration"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/4/configuration_descriptor"/>
  <target id="http://testserver/api/v1/targets/1">vsphere1.eng.rpath.com</target>
  <name>vsphere1 002</name>
  <network_address>
    <address>vsphere1-002</address>
  </network_address>
  <local_uuid/>
  <project_branch/>
  <management_interface/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <current_state id="http://testserver/api/v1/inventory/system_states/1">
    <system_state_id>1</system_state_id>
    <description>Unmanaged</description>
    <name>unmanaged</name>
    <created_date>2010-09-23T13:30:14.100890+00:00</created_date>
  </current_state>
  <created_date>2010-09-23T13:30:14.295974+00:00</created_date>
  <target_system_description/>
  <source_image/>
</system>
"""

credentials_xml = """\
<?xml version="1.0"?>
<credentials>
  <ssl_client_certificate>newsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>newsslclientkey</ssl_client_key>
</credentials>
"""

ssh_credentials_xml = """\
<?xml version="1.0"?>
<credentials>
  <key>sshKeyContentsGoesHere</key>
  <password>osOrUnlockPassword</password>
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
<credentials id="http://testserver/api/v1/inventory/systems/3/credentials">
  <ssl_client_certificate>newsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>newsslclientkey</ssl_client_key>
</credentials>
"""

credentials_put_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/v1/inventory/systems/3/credentials">
  <ssl_client_certificate>updatedsslclientcertificate</ssl_client_certificate>
  <ssl_client_key>updatedsslclientkey</ssl_client_key>
</credentials>
"""

credentials_wmi_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/v1/inventory/systems/3/credentials">
  <domain>testDomain</domain>
  <user>testUser</user>
  <password>testPassword</password>
</credentials>
"""

credentials_wmi_put_resp_xml = """\
<?xml version="1.0"?>
<credentials id="http://testserver/api/v1/inventory/systems/3/credentials">
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

configuration_put_xml = """\
<?xml version="1.0"?>
<configuration>
  <http_port>890</http_port>
</configuration>
"""

configuration_descriptor_xml = """\
<configuration_descriptor xmlns="http://www.rpath.com/permanent/descriptor-1.1.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd" version="1.1">
  <dataFields/>
  <metadata/>
</configuration_descriptor>"""

system_assimilator_xml = """\
<job>
  <job_type id='https://localhost/api/v1/inventory/event_types/12'>system assimilation</job_type>
  <descriptor id='https://localhost/api/v1/inventory/systems/3/descriptors/assimilation'/>
  <descriptor_data/>
</job>
"""

system_post_forge_object = """<?xml version="1.0" encoding="UTF-8"?>
<system>
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <ssl_client_key>testsystemsslclientkey</ssl_client_key>
  <out_of_date>false</out_of_date>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <networks>
    <network>
      <active/>
      <device_name>eth0</device_name>
      <dns_name>testnetwork.example.com</dns_name>
      <ip_address>1.1.1.1</ip_address>
      <ipv6_address/>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <pinned/>
    </network>
  </networks>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <project_branch_stage/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/9999">Should Not Exist</management_interface>
  <source_image/>
</system>"""

retirement_xml = """
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <networks/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/3">Secure Shell (SSH)</management_interface>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  <actions>
    <action>
      <name>Assimilate system</name>
      <job_type id="http://testserver/api/v1/inventory/event_types/12"/>
      <enabled>true</enabled>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/assimilation"/>
      <key>system_assimilation</key>
      <description>Assimilate system</description>
    </action>
    <action>
      <name>System capture</name>
      <job_type id="http://testserver/api/v1/inventory/event_types/21"/>
      <enabled>false</enabled>
      <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/capture"/>
      <key>system_capture</key>
      <description>Capture a system's image</description>
    </action>
    <action>
        <description>Apply system configuration</description>
        <descriptor id="http://testserver/api/v1/inventory/systems/3/descriptors/configure"/>
        <enabled>False</enabled>
        <job_type id="http://testserver/api/v1/inventory/event_types/27"/>
        <key>system_apply_configuration</key>
        <name>Apply system configuration</name>
     </action>
  </actions>
  <has_running_jobs>false</has_running_jobs>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <generated_uuid></generated_uuid>
  <modified_date></modified_date>
  <modified_by></modified_by>
  <ssl_server_certificate></ssl_server_certificate>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname></hostname>
  <created_by></created_by>
  <agent_port>22</agent_port>
  <project_branch_stage></project_branch_stage>
  <system_id>3</system_id>
  <launching_user></launching_user>
  <launch_date></launch_date>
  <ssl_client_certificate></ssl_client_certificate>
  <registration_date></registration_date>
  <project_branch></project_branch>
  <description>ghost</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <target_system_id></target_system_id>
  <has_active_jobs>false</has_active_jobs>
  <target_system_name></target_system_name>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
  </jobs>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <source_image></source_image>
  <name>blinky</name>
  <out_of_date>false</out_of_date>
  <target></target>
  <local_uuid></local_uuid>
  <target_system_state></target_system_state>
  <generated_uuid>%(generatedUuid)s</generated_uuid>
  <current_state>
    <description>Retired</description>
    <name>mothballed</name>
    <system_state_id>12</system_state_id>
  </current_state>
  <project></project>
  <created_date>2011-11-17T18:47:49.469749+00:00</created_date>
  <target_system_description></target_system_description>
</system>
"""

surveys_xml = """
<surveys count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/inventory/systems/3/surveys/" id="http://testserver/api/v1/inventory/systems/3/surveys/" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <survey id="http://testserver/api/v1/inventory/surveys/%(uuid)s">
    <description/>
    <name>x</name>
    <removable>True</removable>
    <uuid>%(uuid)s</uuid>
    <execution_error_count/>
    <overall_compliance>True</overall_compliance>
    <overall_validation>False</overall_validation>
    <updates_pending>False</updates_pending>
    <has_errors>False</has_errors>
    <system id="http://testserver/api/v1/inventory/systems/3"/>
  </survey>
</surveys>
"""

survey_output_xml = """
<survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000">
    <system_model/>
    <system_model_modified_date/>
    <has_system_model>false</has_system_model>
    <config_properties_descriptor/>
    <desired_properties_descriptor/>
    <compliance_summary/>
    <config_compliance/>
    <comment></comment>
    <preview/>
    <removable>True</removable>
    <modified_date>2012-02-03T16:28:08.137616+00:00</modified_date>
    <modified_by id="http://testserver/api/v1/users/2">
      <user_name>JeanValjean1</user_name>
      <full_name></full_name>
    </modified_by>
    <uuid>00000000-0000-4000-0000-000000000000</uuid>
    <tags>
      <tag id="http://testserver/api/v1/inventory/survey_tags/1">
        <survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000"/>
        <name>needs_review</name>
        <tag_id>1</tag_id>
      </tag>
    </tags>
    <windows_patches/>
    <windows_packages/>
    <windows_services/>
    <rpm_packages>
      <rpm_package id="http://testserver/api/v1/inventory/survey_rpm_packages/1">
        <survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000"/>
        <rpm_package_id>1</rpm_package_id>
        <rpm_package_info id="http://testserver/api/v1/inventory/rpm_package_info/1">
          <description>enterprise middleware abstraction layer</description>
          <epoch>0</epoch>
          <version>5</version>
          <architecture>x86_64</architecture>
          <signature>X</signature>
          <release>6</release>
          <name>asdf</name>
        </rpm_package_info>
        <install_date>2012-02-03T16:28:08.177050+00:00</install_date>
      </rpm_package>
    </rpm_packages>
    <description></description>
    <system id="http://testserver/api/v1/inventory/systems/3"/>
    <created_by id="http://testserver/api/v1/users/2">
      <user_name>JeanValjean1</user_name>
      <full_name></full_name>
    </created_by>
    <created_date>2012-02-03T16:28:08.137524+00:00</created_date>
    <services>
      <service id="http://testserver/api/v1/inventory/survey_services/1">
        <status>is maybe doing stuff</status>
        <survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000"/>
        <running>false</running>
        <service_info id="http://testserver/api/v1/inventory/service_info/1">
          <name>httpd</name>
          <autostart>1</autostart>
          <runlevels>3,4,5</runlevels>
        </service_info>
        <service_id>1</service_id>
      </service>
    </services>
    <conary_packages>
      <conary_package id="http://testserver/api/v1/inventory/survey_conary_packages/1">
        <conary_package_id>1</conary_package_id>
        <survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000"/>
        <install_date>2012-02-03T16:28:08.169386+00:00</install_date>
        <is_top_level>False</is_top_level>
        <conary_package_info id="http://testserver/api/v1/inventory/conary_package_info/1">
          <description>Type-R</description>
          <name>jkl</name>
          <version>7</version>
          <architecture>ia64</architecture>
          <signature>X</signature>
          <rpm_package_info>
            <name>asdf</name>
            <epoch>0</epoch>
            <version>5</version>
            <architecture>x86_64</architecture>
            <signature>X</signature>
            <release>6</release>
            <rpm_package_id>1</rpm_package_id>
            <description>enterprise middleware abstraction layer</description>
          </rpm_package_info>
          <flavor>orange</flavor>
          <revision>8</revision>
        </conary_package_info>
      </conary_package>
    </conary_packages>
    <name>x</name>
    <config_properties></config_properties>
    <desired_properties></desired_properties>
    <observed_properties></observed_properties>
    <discovered_properties></discovered_properties>
    <validation_report></validation_report>
</survey>
"""

survey_preview_template = """
<preview>
<observed>group-foo-appliance/1.2.3.3 possibly-other-junk/1.2.3.4</observed>
<desired>group-foo-appliance/1.2.3.4</desired>
<compliant>true</compliant>
<conary_package_changes>
<conary_package_change>
<type>removed</type>
<!-- ASK: since this won't be in the database, we can forego IDs -->
<removed_conary_package>
<name>blah</name>
<version>blah</version>
<signature>X</signature>
<architecture>arch</architecture>
<flavor>orange</flavor>
</removed_conary_package>
</conary_package_change>
<conary_package_change>
<type>added</type>
<added_conary_package>
<name>blah</name>
<version>blah</version>
<architecture>blah</architecture>
<signature>X</signature>
<flavor>orange</flavor>
</added_conary_package>
</conary_package_change>
<conary_package_change>
<type>changed</type>
<from>
<name>name</name>
<version>1</version>
<architecture>arch</architecture>
<signature>X</signature>
</from>
<to>
<name>name</name>
<version>2</version>
<architecture>arch</architecture>
<signature>X</signature>
</to>
<conary_package_diff>
<version>
<from>1</from>
<to>2</to>
</version>
</conary_package_diff>
</conary_package_change>
<!-- IMPORTANT: nothing in the preview but conary packages -->
</conary_package_changes>
</preview>
"""

survey_preview = survey_preview_template
survey_preview_alt = survey_preview_template

# NOTE: the examples in the XML items below are not domain-specific, but structural
# so if "STIG checker" doesn't make sense in all examples, don't take it literally
# see RCE-303

config_properties_template = """
<config_properties>
  <values> <!-- bogus element to see if we rename it to 'configuration' -->
  <apache_configuration>
    <port>8080</port>
    <processInfo>
      <!-- This is a compound data type field -->
      <user>nobody</user>
      <group>nobody</group>
    </processInfo>
    <vhosts list="true">
      <vhost>
        <serverName>vhost1.example.com</serverName>
        <documentRoot>/home/vhost1/public_html</documentRoot>
      </vhost>
      <vhost>
        <serverName>vhost2.example.com</serverName>
        <documentRoot>/home/vhost2/public_html</documentRoot>
      </vhost>
    </vhosts>
    <aliases list="true">
      <alias>
        <handle>/images</handle>
        <directory>/srv/www/images</directory>
      </alias>
      <alias>
        <handle>/icons</handle>
        <directory>/srv/www/icons</directory>
      </alias>
      <alias>
        <handle>/robots.txt</handle>
        <directory>/home/admin/hg/web-docs/robots.txt</directory>
      </alias>
    </aliases>
  </apache_configuration>
  <disa_stig_compliance_checker>
    <dashboardServer>dashboard.eng.rpath.com</dashboardServer>
    <credentials>
      <username>host-123</username>
      <password>my-password-123</password>
    </credentials>
  </disa_stig_compliance_checker>
  </values>
</config_properties>
"""

config_properties = config_properties_template
config_properties_alt = config_properties_template


desired_properties_template = """
<desired_properties>
  <apache_configuration>
    <port>8080</port>
    <processInfo>
      <!-- This is a compound data type field -->
      <user>nobody</user>
      <group>nobody</group>
    </processInfo>
    <vhosts list="true">
      <vhost>
        <serverName>vhost1.example.com</serverName>
        <documentRoot>/home/vhost1/public_html</documentRoot>
      </vhost>
      <vhost>
        <serverName>vhost2.example.com</serverName>
        <documentRoot>/home/vhost2/public_html</documentRoot>
      </vhost>
    </vhosts>
    <aliases list="true">
      <alias>
        <handle>/images</handle>
        <directory>/srv/www/images</directory>
      </alias>
      <alias>
        <handle>/icons</handle>
        <directory>/srv/www/icons</directory>
      </alias>
      <alias>
        <handle>/robots.txt</handle>
        <directory>/home/admin/hg/web-docs/robots.txt</directory>
      </alias>
    </aliases>
  </apache_configuration>
  <disa_stig_compliance_checker>
    <dashboardServer>dashboard.eng.rpath.com</dashboardServer>
    <credentials>
      <username>host-123</username>
      <password>my-password-123</password>
    </credentials>
  </disa_stig_compliance_checker>
</desired_properties>
"""

desired_properties = desired_properties_template
desired_properties_alt = desired_properties_template

observed_properties_template = """
<observed_properties>
  <extensions>
    <apache_configuration>
      <name>Apache configuration</name> 
      <port>8081</port>
    </apache_configuration>
  </extensions>
  <errors>
    <apache_configuration>
      <!-- Overall the reader succeeded (hypothetically) -->
      <success>true</success>
      <error_list>
        <error>
          <!-- Global error -->
          <code>500</code>
          <message>General error: apache not running</message>
          <detail>Lazy sysadmin didn't start apache</detail>
        </error>
        <error>
          <!-- Error processing just one of the fields -->
          <!-- Deep fields will be separated by / -->
          <field>processInfo/user</field>
          <code>1</code>
          <message>Apache claims user blah, user blah does not exist</message>
          <detail>Traceback: blah</detail>
        </error>
      </error_list>
    </apache_configuration>
    <disa_stig_compliance_checker>
      <success>false</success>
      <error_list>
        <error>
          <!-- Global error, the whole reader plugin failed -->
          <code>100</code>
          <message>Error: DISA compliance checker segfaulted</message>
          <detail>Core dump here</detail>
        </error>
      </error_list>
    </disa_stig_compliance_checker>
  </errors>
</observed_properties>
"""

observed_properties = observed_properties_template
observed_properties_alt = observed_properties_template.replace("Lazy","Studious")

discovered_properties_template = """
<discovered_properties>
  <extensions>
    <apache_configuration>
      <name>Apache Configuration Checker</name>
      <probes>
        <port>
          <name>Apache Port Check</name>
          <value content_type="text/html" encoding="base64">80</value>
        </port>
        <port>
          <name>Foo Port Check</name>
          <value content_type="text/html" encoding="base64">5000</value>
        </port>
      </probes>
    </apache_configuration>
  </extensions>
  <errors>
    <apache_configuration>
      <!-- Overall the reader succeeded (hypothetically) -->
      <success>true</success>
      <error_list>
        <error>
          <!-- Global error -->
          <code>500</code>
          <message>General error: apache not running</message>
          <detail>Lazy sysadmin didn't start apache</detail>
        </error>
        <error>
          <code>1</code>
          <message>Apache claims user blah, user blah does not exist</message>
          <detail>Traceback: blah</detail>
        </error>
      </error_list>
    </apache_configuration>
    <disa_stig_compliance_checker>
      <success>false</success>
      <error_list>
        <error>
          <!-- Global error, the whole reader plugin failed -->
          <code>100</code>
          <message>Error: DISA compliance checker segfaulted</message>
          <detail>Core dump here</detail>
        </error>
      </error_list>
    </disa_stig_compliance_checker>
  </errors>
</discovered_properties>
"""

discovered_properties = discovered_properties_template
discovered_properties_alt = discovered_properties_template.replace("false","true").replace("5000","5001")

validation_report_template = """
<validation_report>
  <status>fail</status>
  <extensions>
    <apache_configuration>
      <name>Apache Configuration Checker</name>
      <status>fail</status>
      <message>Same as in the probes below</message>
      <details/>
      <probes>
        <port>
          <name>Apache Port Check</name>
          <status>fail</status>
          <message>Apache not running on port</message>
          <details content_type="text/html" encoding="base64">base64-encoded HTML here</details>
        </port>
        <port>
          <name>Apache Port Check</name>
          <status>fail</status>
          <message>Apache not running on port</message>
          <details content_type="text/html" encoding="base64">base64-encoded HTML here</details>
        </port>
      </probes>
    </apache_configuration>
    FILLER1
    FILLER2
  </extensions>
  <errors>
    <apache_configuration>
      <!-- Overall the handler succeeded (hypothetically) -->
      <success>true</success>
      <error_list>
        <error>
          <!-- Global error -->
          <code>500</code>
          <message>General error: apache not running</message>
          <detail>Lazy sysadmin didn't start apache</detail>
        </error>
        <error>
          <code>1</code>
          <message>Apache claims user blah, user blah does not exist</message>
          <detail>Traceback: blah</detail>
        </error>
      </error_list>
    </apache_configuration>
    <disa_stig_compliance_checker>
      <success>false</success>
      <error_list>
        <error>
          <!-- Global error, the whole reader plugin failed -->
          <code>100</code>
          <message>Error: DISA compliance checker segfaulted</message>
          <detail>Core dump here</detail>
        </error>
      </error_list>
    </disa_stig_compliance_checker>
  </errors>
</validation_report>
"""

stub1 = """
<xyz_configuration>
      <name>XYZ Configuration Checker</name>
      <status>fail</status>
      <message>Same as in the probes below</message>
      <details/>
      <probes>
        <port>
          <name>XYZ Port Check</name>
          <status>fail</status>
          <message>XYZ not running on port</message>
          <details content_type="text/html" encoding="base64">base64-encoded HTML here</details>
        </port>
      </probes>
</xyz_configuration>
"""

stub2 = """
<abc_configuration>
      <name>ABC Configuration Checker</name>
      <status>fail</status>
      <message>Same as in the probes below</message>
      <details/>
      <probes>
        <port>
          <name>ABC Port Check</name>
          <status>fail</status>
          <message>ABC not running on port</message>
          <details content_type="text/html" encoding="base64">base64-encoded HTML here</details>
        </port>
      </probes>
</abc_configuration>
"""


validation_report = validation_report_template.replace("FILLER1",stub1).replace("FILLER2","")
validation_report_alt = validation_report_template.replace("false","true").replace("not running on port","jump on it").replace("FILLER1","").replace("FILLER2",stub2).replace("user blah does not exist","user quota exceeded")

# input without ids
# FIXME -- created_by/modified_by should be nullable for system
#          user?

system_model = """
  <system_model>
    <contents>search group-haystack=haystack.rpath.com@rpath:haystack-1/1-1-1
install group-haystack
install needle
</contents>
    <modified_date>1234567890</modified_date>
  </system_model>
"""

system_model_ret = """
  <system_model>search group-haystack=haystack.rpath.com@rpath:haystack-1/1-1-1
install group-haystack
install needle
</system_model>
  <system_model_modified_date>2009-02-13T23:31:30+00:00</system_model_modified_date>
  <has_system_model>true</has_system_model>
"""

survey_input_xml_template = """
<survey>
    %(system_model)s
    %(config_properties)s
    %(observed_properties)s
    %(discovered_properties)s
    %(validation_report)s
    %(survey_preview)s
    <config_properties_descriptor><blarg/></config_properties_descriptor>
    <comment></comment>
    <uuid>1234</uuid>
    <removable>False</removable>
    <tags>
      <tag>
        <name>needs_review</name>
      </tag>
    </tags>
    <rpm_packages>
      <rpm_package id="1">
        <rpm_package_info>
          <description>enterprise middleware abstraction layer</description>
          <epoch>0</epoch>
          <version>5</version>
          <architecture>x86_64</architecture>
          <signature>X</signature>
          <release>6</release>
          <name>asdf</name>
        </rpm_package_info>
        <install_date>2012-02-03T16:28:08.177050+00:00</install_date>
      </rpm_package>
    </rpm_packages>
    <description></description>
    <system id="http://testserver/api/v1/inventory/systems/3"/>
    <created_by id="http://testserver/api/v1/users/2"/>
    <created_date>0</created_date>
    <services>
      <service id="2">
        <status>is maybe doing stuff</status>
        <running>false</running>
        <service_info>
          <name>httpd</name>
          <autostart>1</autostart>
          <runlevels>3,4,5</runlevels>
        </service_info>
      </service>
    </services>
    <conary_packages>
      <conary_package id="3">
        <install_date>2012-02-03T16:28:08.169386+00:00</install_date>
        <is_top_level>true</is_top_level>
        <conary_package_info>
          <description>Type-R</description>
          <name>jkl</name>
          <version>7</version>
          <architecture>ia64</architecture>
          <signature>X</signature>
          <rpm_package_info id="1">
            <name>asdf</name>
            <epoch>0</epoch>
            <version>5</version>
            <architecture>x86_64</architecture>
            <signature>X</signature>
            <release>6</release>
            <description>enterprise middleware abstraction layer</description>
          </rpm_package_info>
          <flavor>orange</flavor>
          <revision>8</revision>
        </conary_package_info>
      </conary_package>
    </conary_packages>
    <name>x</name>
</survey>
"""

survey_input_xml = (survey_input_xml_template % dict(
    system_model=system_model,
    config_properties=config_properties, 
    observed_properties=observed_properties, 
    discovered_properties=discovered_properties, 
    validation_report=validation_report,
    survey_preview=survey_preview
))

survey_input_xml_alt = (survey_input_xml_template % dict(
    system_model="",
    config_properties=config_properties_alt, 
    observed_properties=observed_properties_alt, 
    discovered_properties=discovered_properties_alt, 
    validation_report=validation_report_alt,
    survey_preview=survey_preview_alt
)).replace("1234", "99999")

survey_output_xml2 = """
<survey id="http://testserver/api/v1/inventory/surveys/1234">
  <comment/>
  <compliance_summary>
    <config_execution>
      <compliant>False</compliant>
      <failure_count>3</failure_count>
    </config_execution>
    <config_sync>
      <compliant>False</compliant>
    </config_sync>
    <overall>
      <compliant>False</compliant>
    </overall>
    <software>
      <compliant>False</compliant>
      <message>0 added, 0 removed, 0 changed</message>
    </software>
  </compliance_summary>
  <conary_packages>
    <conary_package id="http://testserver/api/v1/inventory/survey_conary_packages/1">
      <conary_package_id>1</conary_package_id>
      <conary_package_info id="http://testserver/api/v1/inventory/conary_package_info/1">
        <architecture>ia64</architecture>
        <description>Type-R</description>
        <flavor>orange</flavor>
        <name>jkl</name>
        <revision>8</revision>
        <rpm_package_info>
          <architecture>x86_64</architecture>
          <description>enterprise middleware abstraction layer</description>
          <epoch>0</epoch>
          <name>asdf</name>
          <release>6</release>
          <rpm_package_id>1</rpm_package_id>
          <signature>X</signature>
          <version>5</version>
        </rpm_package_info>
        <signature>X</signature>
        <version>7</version>
      </conary_package_info>
      <install_date>2012-02-03T16:28:08.169386+00:00</install_date>
      <is_top_level>True</is_top_level>
      <survey id="http://testserver/api/v1/inventory/surveys/1234"/>
    </conary_package>
  </conary_packages>
  <config_compliance>
    <compliant>False</compliant>
    <config_values>
      <config_value>
        <desired>8080</desired>
        <key>port</key>
        <keypath>/apache_configuration/port</keypath>
        <read>8081</read>
      </config_value>
    </config_values>
  </config_compliance>
  <config_properties>
    <apache_configuration>
      <aliases list="True">
        <alias>
          <directory>/srv/www/images</directory>
          <handle>/images</handle>
        </alias>
        <alias>
          <directory>/srv/www/icons</directory>
          <handle>/icons</handle>
        </alias>
        <alias>
          <directory>/home/admin/hg/web-docs/robots.txt</directory>
          <handle>/robots.txt</handle>
        </alias>
      </aliases>
      <port>8080</port>
      <processInfo>
        <group>nobody</group>
        <user>nobody</user>
      </processInfo>
      <vhosts list="True">
        <vhost>
          <documentRoot>/home/vhost1/public_html</documentRoot>
          <serverName>vhost1.example.com</serverName>
        </vhost>
        <vhost>
          <documentRoot>/home/vhost2/public_html</documentRoot>
          <serverName>vhost2.example.com</serverName>
        </vhost>
      </vhosts>
    </apache_configuration>
    <disa_stig_compliance_checker>
      <credentials>
        <password>my-password-123</password>
        <username>host-123</username>
      </credentials>
      <dashboardServer>dashboard.eng.rpath.com</dashboardServer>
    </disa_stig_compliance_checker>
  </config_properties>
  <config_properties_descriptor>
    <blarg/>
  </config_properties_descriptor>
  <description/>
  <desired_properties>
    <apache_configuration>
      <aliases list="True">
        <alias>
          <directory>/srv/www/images</directory>
          <handle>/images</handle>
        </alias>
        <alias>
          <directory>/srv/www/icons</directory>
          <handle>/icons</handle>
        </alias>
        <alias>
          <directory>/home/admin/hg/web-docs/robots.txt</directory>
          <handle>/robots.txt</handle>
        </alias>
      </aliases>
      <port>8080</port>
      <processInfo>
        <group>nobody</group>
        <user>nobody</user>
      </processInfo>
      <vhosts list="True">
        <vhost>
          <documentRoot>/home/vhost1/public_html</documentRoot>
          <serverName>vhost1.example.com</serverName>
        </vhost>
        <vhost>
          <documentRoot>/home/vhost2/public_html</documentRoot>
          <serverName>vhost2.example.com</serverName>
        </vhost>
      </vhosts>
    </apache_configuration>
    <disa_stig_compliance_checker>
      <credentials>
        <password>my-password-123</password>
        <username>host-123</username>
      </credentials>
      <dashboardServer>dashboard.eng.rpath.com</dashboardServer>
    </disa_stig_compliance_checker>
  </desired_properties>
  <desired_properties_descriptor>
    <configuration_descriptor xsi_schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd" version="1.1">
      <dataFields/>
      <metadata/>
    </configuration_descriptor>
  </desired_properties_descriptor>
  <discovered_properties>
    <errors>
      <apache_configuration>
        <error_list>
          <error>
            <code>500</code>
            <detail>Lazy sysadmin didn't start apache</detail>
            <message>General error: apache not running</message>
          </error>
          <error>
            <code>1</code>
            <detail>Traceback: blah</detail>
            <message>Apache claims user blah, user blah does not exist</message>
          </error>
        </error_list>
        <success>True</success>
      </apache_configuration>
      <disa_stig_compliance_checker>
        <error_list>
          <error>
            <code>100</code>
            <detail>Core dump here</detail>
            <message>Error: DISA compliance checker segfaulted</message>
          </error>
        </error_list>
        <success>False</success>
      </disa_stig_compliance_checker>
    </errors>
    <extensions>
      <apache_configuration>
        <name>Apache Configuration Checker</name>
        <probes>
          <port>
            <name>Apache Port Check</name>
            <value content_type="text/html" encoding="base64">80</value>
          </port>
          <port>
            <name>Foo Port Check</name>
            <value content_type="text/html" encoding="base64">5000</value>
          </port>
        </probes>
      </apache_configuration>
    </extensions>
  </discovered_properties>
  <name>blinky</name>
  <observed_properties>
    <errors>
      <apache_configuration>
        <error_list>
          <error>
            <code>500</code>
            <detail>Lazy sysadmin didn't start apache</detail>
            <message>General error: apache not running</message>
          </error>
          <error>
            <code>1</code>
            <detail>Traceback: blah</detail>
            <field>processInfo/user</field>
            <message>Apache claims user blah, user blah does not exist</message>
          </error>
        </error_list>
        <success>True</success>
      </apache_configuration>
      <disa_stig_compliance_checker>
        <error_list>
          <error>
            <code>100</code>
            <detail>Core dump here</detail>
            <message>Error: DISA compliance checker segfaulted</message>
          </error>
        </error_list>
        <success>False</success>
      </disa_stig_compliance_checker>
    </errors>
    <extensions>
      <apache_configuration>
        <port>8081</port>
      </apache_configuration>
    </extensions>
  </observed_properties>
  <preview>
    <compliant>True</compliant>
    <conary_package_changes>
      <conary_package_change>
        <removed_conary_package>
          <architecture>arch</architecture>
          <flavor>orange</flavor>
          <name>blah</name>
          <signature>X</signature>
          <version>blah</version>
        </removed_conary_package>
        <type>removed</type>
      </conary_package_change>
      <conary_package_change>
        <added_conary_package>
          <architecture>blah</architecture>
          <flavor>orange</flavor>
          <name>blah</name>
          <signature>X</signature>
          <version>blah</version>
        </added_conary_package>
        <type>added</type>
      </conary_package_change>
      <conary_package_change>
        <conary_package_diff>
          <version>
            <from>1</from>
            <to>2</to>
          </version>
        </conary_package_diff>
        <from>
          <architecture>arch</architecture>
          <name>name</name>
          <signature>X</signature>
          <version>1</version>
        </from>
        <to>
          <architecture>arch</architecture>
          <name>name</name>
          <signature>X</signature>
          <version>2</version>
        </to>
        <type>changed</type>
      </conary_package_change>
    </conary_package_changes>
    <desired>group-foo-appliance/1.2.3.4</desired>
    <observed>group-foo-appliance/1.2.3.3 possibly-other-junk/1.2.3.4</observed>
  </preview>
  <removable>True</removable>
  <rpm_packages>
    <rpm_package id="http://testserver/api/v1/inventory/survey_rpm_packages/1">
      <install_date>2012-02-03T16:28:08.177050+00:00</install_date>
      <rpm_package_id>1</rpm_package_id>
      <rpm_package_info id="http://testserver/api/v1/inventory/rpm_package_info/1">
        <architecture>x86_64</architecture>
        <description>enterprise middleware abstraction layer</description>
        <epoch>0</epoch>
        <name>asdf</name>
        <release>6</release>
        <signature>X</signature>
        <version>5</version>
      </rpm_package_info>
      <survey id="http://testserver/api/v1/inventory/surveys/1234"/>
    </rpm_package>
  </rpm_packages>
  <services>
    <service id="http://testserver/api/v1/inventory/survey_services/1">
     <running>False</running>
      <service_id>1</service_id>
      <service_info id="http://testserver/api/v1/inventory/service_info/1">
        <autostart>1</autostart>
        <name>httpd</name>
        <runlevels>3,4,5</runlevels>
      </service_info>
      <status>is maybe doing stuff</status>
      <survey id="http://testserver/api/v1/inventory/surveys/1234"/>
    </service>
  </services>
  <system id="http://testserver/api/v1/inventory/systems/3"/>
  %(system_model)s
  <tags>
    <tag id="http://testserver/api/v1/inventory/survey_tags/1">
      <name>needs_review</name>
      <survey id="http://testserver/api/v1/inventory/surveys/1234"/>
      <tag_id>1</tag_id>
    </tag>
  </tags>
  <uuid>1234</uuid>
  <validation_report>
    <errors>
      <apache_configuration>
        <error_list>
          <error>
            <code>500</code>
            <detail>Lazy sysadmin didn't start apache</detail>
            <message>General error: apache not running</message>
          </error>
          <error>
            <code>1</code>
            <detail>Traceback: blah</detail>
            <message>Apache claims user blah, user blah does not exist</message>
          </error>
        </error_list>
        <success>True</success>
      </apache_configuration>
      <disa_stig_compliance_checker>
        <error_list>
          <error>
            <code>100</code>
            <detail>Core dump here</detail>
            <message>Error: DISA compliance checker segfaulted</message>
          </error>
        </error_list>
        <success>False</success>
      </disa_stig_compliance_checker>
    </errors>
    <extensions>
      <apache_configuration>
        <details/>
        <message>Same as in the probes below</message>
        <name>Apache Configuration Checker</name>
        <probes>
          <port>
            <details content_type="text/html" encoding="base64">80</details>
            <message>Apache not running on port</message>
            <name>Apache Port Check</name>
            <status>fail</status>
          </port>
          <port>
            <details content_type="text/html" encoding="base64">5000</details>
            <message>Apache not running on port</message>
            <name>Foo Port Check</name>
            <status>fail</status>
          </port>
        </probes>
        <status>fail</status>
      </apache_configuration>
    </extensions>
    <status>fail</status>
  </validation_report>
  <windows_packages/>
  <windows_patches/>
  <windows_services/>
</survey>
""" % dict(system_model=system_model_ret)

# FIXME: add tests trying to clobber fields it should not clobber
# or if it can erase things

survey_mod_xml="""
<survey id='http://testserver/api/v1/inventory/surveys/1234'>
    <comment>Here is a comment</comment>
    <uuid>1234</uuid>
    <name>Here is a name</name>
    <removable>True</removable>
    <tags>
      <tag>
        <name>onfire</name>
      </tag>
      <tag>
        <name>stat</name>
      </tag>
    </tags>
</survey>
"""

system_configuration_xml = """
<job>
<descriptor id='http://testserver/api/v1/inventory/systems/%s/descriptors/configure'/>
<descriptor_data />
<job_type id='https://testserver/api/v1/inventory/event_types/27' href='https://testserver/api/v1/inventory/event_types/27' />
</job>
"""


