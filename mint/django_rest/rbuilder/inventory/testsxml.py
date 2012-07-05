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
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
    <description>Initial synchronization pending</description>
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
    <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
      <description>Initial synchronization pending</description>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
    <description>Initial synchronization pending</description>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
    <description>Initial synchronization pending</description>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
    <description>Initial synchronization pending</description>
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
    <generated_uuid/>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/v1/inventory/systems/2/installed_software"/>
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
      <description>Initial synchronization pending</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
    <generated_uuid>testsystemgenerateduuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <hostname/>
    <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
      <description>Initial synchronization pending</description>
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
      <description>Initial synchronization pending</description>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
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
    <description>Initial synchronization pending</description>
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
    <installed_software />
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
  <target/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
    <description>Initial synchronization pending</description>
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
    <event_type id="http://testserver/api/v1/inventory/event_types/1"/>
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

get_installed_software_xml = """\
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software/">
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%%3D/clover.eng.rpath.com%%40rpath%%3Aclover-1-devel/1-2-1%%5B%%7E%%21dom0%%2C%%7E%%21domU%%2Cvmware%%2C%%7E%%21xen%%20is%%3A%%20x86%%28i486%%2Ci586%%2Ci686%%2Csse%%2Csse2%%29%%5D">
      <available_updates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.12</ordering>
          <revision>change me gently</revision>
          <version_id>1</version_id>
        </version>
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
      <is_top_level>True</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>group-clover-appliance</name>
      <out_of_date>true</out_of_date>
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
      <available_updates>
        <version>
          <flavor>desktop is: x86_64</flavor>
          <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
          <label>contrib.rpath.org@rpl:2</label>
          <ordering>1234567890.12</ordering>
          <revision>23.0.60cvs20080523-1-0.1</revision>
          <version_id>4</version_id>
        </version>
      </available_updates>
      <flavor>desktop is: x86_64</flavor>
      <is_top_level>False</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <last_available_update_refresh>%s</last_available_update_refresh>
      <name>emacs</name>
      <out_of_date/>
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
      <is_top_level>True</is_top_level>
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
      <is_top_level>False</is_top_level>
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
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>%%s</created_date>
  <source_image/>
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
<system id="http://testserver/api/v1/inventory/systems/3">
  %s
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <event_uuid>testeventuuid</event_uuid>
</system>
""" % installed_software_post_xml

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
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>2</system_state_id>
  </current_state>
  <created_date>2010-08-23T21:41:31.278455+00:00</created_date>
  <source_image/>
</system>
""" % installed_software_response_xml

system_available_updates_xml = """\
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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software">
    <trove id="http://testserver/repos/clover/api/trove/group-clover-appliance%3D/clover.eng.rpath.com%40rpath%3Aclover-1-devel/1-2-1%5B%7E%21dom0%2C%7E%21domU%2Cvmware%2C%7E%21xen%20is%3A%20x86%28i486%2Ci586%2Ci686%2Csse%2Csse2%29%5D">
      <name>group-clover-appliance</name>
      <out_of_date>true</out_of_date>
      <trove_id>1</trove_id>
      <available_updates>
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.12</ordering>
          <revision>change me gently</revision>
          <version_id>1</version_id>
        </version>
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
      <is_top_level>True</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>emacs</name>
      <out_of_date/>
      <trove_id>2</trove_id>
      <available_updates>
        <version>
          <flavor>desktop is: x86_64</flavor>
          <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
          <label>contrib.rpath.org@rpl:2</label>
          <ordering>1234567890.12</ordering>
          <revision>23.0.60cvs20080523-1-0.1</revision>
          <version_id>4</version_id>
        </version>
      </available_updates>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>4</version_id>
      </version>
      <last_available_update_refresh>2010-08-27T12:21:59.815100+00:00</last_available_update_refresh>
      <is_top_level>False</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>desktop is: x86_64</flavor>
    </trove>
  </installed_software>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <active/>
      <created_date>2010-08-27T12:21:59.801387+00:00</created_date>
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
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <out_of_date>True</out_of_date>
  <registration_date/>
  <description>testsystemdescription</description>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <target/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <system_state_id>3</system_state_id>
  </current_state>
  <created_date>2010-08-27T12:21:59.800269+00:00</created_date>
  <source_image/>
</system>
"""

system_apply_updates_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software">
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
        <version>
          <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
          <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-2-1</full>
          <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
          <ordering>1234567890.12</ordering>
          <revision>change me gently</revision>
          <version_id>1</version_id>
        </version>
      </available_updates>
      <version>
        <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
        <full>/clover.eng.rpath.com@rpath:clover-1-devel/1-3-1</full>
        <label>clover.eng.rpath.com@rpath:clover-1-devel</label>
        <ordering>1234567891.13</ordering>
        <revision>1-3-1</revision>
        <version_id>2</version_id>
      </version>
      <last_available_update_refresh>2010-08-27T12:21:59.802463+00:00</last_available_update_refresh>
      <is_top_level>True</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/emacs%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>emacs</name>
      <trove_id>2</trove_id>
      <available_updates>
        <version>
          <flavor>desktop is: x86_64</flavor>
          <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
          <label>contrib.rpath.org@rpl:2</label>
          <ordering>1234567890.12</ordering>
          <revision>23.0.60cvs20080523-1-0.1</revision>
          <version_id>4</version_id>
        </version>
      </available_updates>
      <version>
        <flavor>desktop is: x86_64</flavor>
        <full>/contrib.rpath.org@rpl:devel//2/23.0.60cvs20080523-1-0.1</full>
        <label>contrib.rpath.org@rpl:2</label>
        <ordering>1234567890.12</ordering>
        <revision>23.0.60cvs20080523-1-0.1</revision>
        <version_id>4</version_id>
      </version>
      <last_available_update_refresh>2010-08-27T12:21:59.815100+00:00</last_available_update_refresh>
      <is_top_level>False</is_top_level>
      <is_top_level_item>True</is_top_level_item>
      <flavor>desktop is: x86_64</flavor>
    </trove>
  </installed_software>
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
  <installed_software id="http://testserver/api/v1/inventory/systems/4/installed_software"/>
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

configuration_post_resp_xml = """\
<?xml version="1.0"?>
<configuration id="http://testserver/api/v1/inventory/systems/3/configuration">
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
<configuration id="http://testserver/api/v1/inventory/systems/3/configuration">
  <http_port>890</http_port>
</configuration>
"""

configuration_descriptor_xml = """\
<configuration_descriptor xmlns="http://www.rpath.com/permanent/descriptor-1.1.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd" version="1.1">
  <dataFields/>
  <metadata/>
</configuration_descriptor>"""

system_installed_software_version_stage_xml = """\
<?xml version="1.0"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <configuration_applied>False</configuration_applied>
  <configuration_set>False</configuration_set>
  <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
  <management_interface id="http://testserver/api/v1/inventory/management_interfaces/1">Common Information Model (CIM)</management_interface>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <name>chater-foo</name>
    <short_name>chater-foo</short_name>
  </project>
  <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
  <has_running_jobs>True</has_running_jobs>
  <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <network_address>
    <address>1.1.1.1</address>
  </network_address>
  <networks>
    <network id="http://testserver/api/v1/inventory/networks/2">
      <ipv6_address/>
      <network_id>2</network_id>
      <dns_name>testnetwork.example.com</dns_name>
      <system id="http://testserver/api/v1/inventory/systems/3"/>
      <pinned/>
      <device_name>eth0</device_name>
      <netmask>255.255.255.0</netmask>
      <port_type>lan</port_type>
      <created_date>2010-11-10T22:52:26.350321+00:00</created_date>
      <active/>
      <ip_address>1.1.1.1</ip_address>
    </network>
  </networks>
  <ssl_server_certificate>testsystemsslservercertificate</ssl_server_certificate>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>3</system_id>
  <launching_user/>
  <launch_date/>
  <ssl_client_certificate>testsystemsslclientcertificate</ssl_client_certificate>
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software">
    <trove id="http://testserver/repos/chater-foo/api/trove/group-chater-foo-appliance%3D/chater-foo.eng.rpath.com%40rpath%3Achater-foo-1-devel/1-2-1%5Bis%3A%20x86%5D">
      <name>group-chater-foo-appliance</name>
      <out_of_date/>
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
      <is_top_level>True</is_top_level>
      <flavor>is: x86</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/vim%3D/contrib.rpath.org%40rpl%3A2/23.0.60cvs20080523-1-0.1%5Bdesktop%20is%3A%20x86_64%5D">
      <name>vim</name>
      <out_of_date/>
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
      <is_top_level>False</is_top_level>
      <flavor>desktop is: x86_64</flavor>
    </trove>
    <trove id="http://testserver/repos/contrib/api/trove/info-sfcb%3D/contrib.rpath.org%40rpl%3A2/1-1-1%5B%5D">
      <name>info-sfcb</name>
      <out_of_date/>
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
      <is_top_level>False</is_top_level>
      <flavor/>
    </trove>
  </installed_software>
  <target_system_id/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
  </jobs>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
  <registration_date/>
  <has_active_jobs>True</has_active_jobs>
  <target_system_name/>
  <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
  <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
  <agent_port>5989</agent_port>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-1/project_branch_stages/Development">
    <name>Development</name>
  </project_branch_stage>
  <out_of_date>false</out_of_date>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <target_system_state/>
  <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-1">
    <name>1</name>
  </project_branch>
  <current_state id="http://testserver/api/v1/inventory/system_states/3">
    <system_state_id>3</system_state_id>
    <description>Initial synchronization pending</description>
    <name>registered</name>
    <created_date>2010-11-10T22:52:26.167013+00:00</created_date>
  </current_state>
  <target/>
  <target_system_description/>
  <created_date>2010-11-10T22:52:26.343993+00:00</created_date>
  <source_image/>
</system>"""

systems_collection_xml = """\
<?xml version="1.0"?>
<!--
Description:
  A collection of systems in inventory
  
Systems Properties:
  event_types - an entry point into system inventory event types
  system - a system resource
  
EventTypes Properties:
  href - the URL to the location of the event types collection

System Properties:
   agent_port - the port used by the system's management interface (CIM, WMI, etc.)
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
   project_branch - the appliance major version of the system
   management_interface - the management interface used to communicate with the system (CIM, WMI, etc.)
   managing_zone - a link to the management zone in which this system resides
   name - the name assigned when system was added to the inventory
   registration_date - the date the system was registered in inventory (UTC)
   ssl_client_certificate - an x509 certificate of an authorized client that can use the system's CIM broker
   ssl_client_key - an x509 private key of an authorized client that can use the system's CIM broker
   ssl_server_certificate - an x509 public certificate of the system's CIM broker
   project_branch_stage - the appliance project_branch_stage of the system
   system_id - the database ID for the system
   system_log - an entry point into the log data for this system
   system_type - the type of the system
   target - the virtual target the system was deployed to (only applies if system is on a virtual target)
   target_system_description - the system description as reported by its target (only applies if system is on a virtual target)
   target_system_id - the system ID as reported by its target (only applies if system is on a virtual target)
   target_system_name - the system name as reported by its target (only applies if system is on a virtual target)
   target_system_state - the system state as reported by its target (only applies if system is on a virtual target)

Identification of Duplicate System Inventory Entries:
  Because systems can enter inventory in a number of different ways, a single system may initially appear in the inventory multiple times.
  The following information is used to identify these duplicate inventory entries:
    1)  local_uuid and generated_uuid - Systems with identical local and generated UUIDs are guaranteed unique.
    2)  target and target_system_id - Virtual targets report a unique ID for each system and thus the combination
           of target and target system ID is guaranteed unique.
    3)  event_uuid - Event UUIDs are used to match system events with an incoming event response and can thus be used
           to lookup a specific system.

Methods: 
  GET:
    Authentication: user
    Response Format:
      <systems>
        <event_types id="http://hostname/api/v1/inventory/event_types/"/>
        <system id="http://hostname/api/v1/inventory/systems/1/">
          ...
        </system>
        <system id="http://hostname/api/v1/inventory/systems/2/">
          ...
        </system>
      </systems>

  POST:
    Authentication: none
    Required Fields:
      Technically only the name field is required.  This could result in duplicate entries in the inventory. 
      The recommended way is to include network information for the system so it can be contacted to initiate the registration process.
    Example:
      <system>
        <name>Billing System Application Server</name>
        <description>The app server for the HR billing system</description>
        <networks>
          <network>
            <dns_name>192.168.1.192</dns_name>
          </network>
        </networks>
      </system>
    
  PUT:
    Authentication: none
    Example:
      <systems>
        <system>
          <name>Billing System Application Server</name>
          <description>The app server for the HR billing system</description>
          <networks>
            <network>
              <dns_name>192.168.1.192</dns_name>
            </network>
          </networks>
        </system>
        <system>
          <name>Billing System File Server</name>
          <description>The file server for the HR billing system</description>
          <networks>
            <network>
              <dns_name>192.168.1.193</dns_name>
            </network>
          </networks>
        </system>
      <systems>
      
  DELETE:
    not supported
-->
<systems count="201" next_page="http://testserver/api/v1/query_sets/5/all;start_index=10;limit=10" num_pages="21" previous_page="" full_collection="http://testserver/api/v1/query_sets/5/all" end_index="9" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10" limit="10" start_index="0">
  <system id="http://testserver/api/v1/inventory/systems/2">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/2/surveys"/>
    <network_address>
      <address>127.0.0.1</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/1">
        <ipv6_address/>
        <network_id>1</network_id>
        <dns_name>127.0.0.1</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/2"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/2/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/2/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/2">rPath Update Service (Infrastructure)</system_type>
    <generated_uuid/>
    <ssl_server_certificate/>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>2</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/2/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/2/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/2/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/2/job_states/4/jobs"/>
    </jobs>
    <description>Local rPath Update Service</description>
    <ssl_client_certificate/>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/2/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/2/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>rPath Update Service</name>
    <local_uuid/>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-08-23T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/3">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/3/surveys"/>
    <network_address>
      <address>127.0.0.3</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/3">
        <ipv6_address/>
        <network_id>3</network_id>
        <dns_name>127.0.0.3</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/3"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/3/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-3-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-3-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>3</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/3/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    </jobs>
    <description>System description 3</description>
    <ssl_client_certificate>system-3-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/3/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/3/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 3</name>
    <local_uuid>system-3-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/4">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/4/surveys"/>
    <network_address>
      <address>127.0.0.4</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/4">
        <ipv6_address/>
        <network_id>4</network_id>
        <dns_name>127.0.0.4</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/4"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/4/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/4/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-4-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-4-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>4</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/4/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/4/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/4/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/4/job_states/4/jobs"/>
    </jobs>
    <description>System description 4</description>
    <ssl_client_certificate>system-4-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/4/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/4/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 4</name>
    <local_uuid>system-4-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/5">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/5/surveys"/>
    <network_address>
      <address>127.0.0.5</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/5">
        <ipv6_address/>
        <network_id>5</network_id>
        <dns_name>127.0.0.5</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/5"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/5/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/5/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-5-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-5-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>5</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/5/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/5/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/5/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/5/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/5/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/5/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/5/job_states/4/jobs"/>
    </jobs>
    <description>System description 5</description>
    <ssl_client_certificate>system-5-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/5/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/5/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 5</name>
    <local_uuid>system-5-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/6">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/6/surveys"/>
    <network_address>
      <address>127.0.0.6</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/6">
        <ipv6_address/>
        <network_id>6</network_id>
        <dns_name>127.0.0.6</dns_name>
        <pinned/>
        <system id="http://testserver/api/v1/inventory/systems/6"/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/6/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/6/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-6-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-6-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>6</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/6/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/6/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/6/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/6/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/6/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/6/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/6/job_states/4/jobs"/>
    </jobs>
    <description>System description 6</description>
    <ssl_client_certificate>system-6-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/6/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/6/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 6</name>
    <local_uuid>system-6-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/7">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/7/surveys"/>
    <network_address>
      <address>127.0.0.7</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/7">
        <ipv6_address/>
        <network_id>7</network_id>
        <dns_name>127.0.0.7</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/7"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/7/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/7/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-7-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-7-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>7</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/7/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/7/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/7/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/7/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/7/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/7/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/7/job_states/4/jobs"/>
    </jobs>
    <description>System description 7</description>
    <ssl_client_certificate>system-7-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/7/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/7/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 7</name>
    <local_uuid>system-7-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/8">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/8/surveys"/>
    <network_address>
      <address>127.0.0.8</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/8">
        <ipv6_address/>
        <network_id>8</network_id>
        <dns_name>127.0.0.8</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/8"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/8/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/8/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-8-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-8-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>8</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/8/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/8/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/8/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/8/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/8/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/8/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/8/job_states/4/jobs"/>
    </jobs>
    <description>System description 8</description>
    <ssl_client_certificate>system-8-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/8/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/8/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 8</name>
    <local_uuid>system-8-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/9">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/9/surveys"/>
    <network_address>
      <address>127.0.0.9</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/9">
        <ipv6_address/>
        <network_id>9</network_id>
        <dns_name>127.0.0.9</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/9"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/9/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/9/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-9-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-9-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>9</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/9/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/9/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/9/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/9/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/9/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/9/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/9/job_states/4/jobs"/>
    </jobs>
    <description>System description 9</description>
    <ssl_client_certificate>system-9-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/9/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/9/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 9</name>
    <local_uuid>system-9-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/10">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/10/surveys"/>
    <network_address>
      <address>127.0.0.10</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/10">
        <ipv6_address/>
        <network_id>10</network_id>
        <dns_name>127.0.0.10</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/10"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/10/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/10/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-10-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-10-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>10</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/10/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/10/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/10/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/10/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/10/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/10/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/10/job_states/4/jobs"/>
    </jobs>
    <description>System description 10</description>
    <ssl_client_certificate>system-10-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/10/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/10/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 10</name>
    <local_uuid>system-10-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/11">
    <configuration_applied>False</configuration_applied>
    <configuration_set>False</configuration_set>
    <surveys id="http://testserver/api/v1/inventory/systems/11/surveys"/>
    <network_address>
      <address>127.0.0.11</address>
    </network_address>
    <networks>
      <network id="http://testserver/api/v1/inventory/networks/11">
        <ipv6_address/>
        <network_id>11</network_id>
        <dns_name>127.0.0.11</dns_name>
        <system id="http://testserver/api/v1/inventory/systems/11"/>
        <pinned/>
        <device_name/>
        <netmask/>
        <port_type/>
        <created_date>2010-10-05T18:36:37+00:00</created_date>
        <active/>
        <ip_address/>
      </network>
    </networks>
    <management_interface/>
    <system_events id="http://testserver/api/v1/inventory/systems/11/system_events"/>
    <project/>
    <configuration_descriptor id="http://testserver/api/v1/inventory/systems/11/configuration_descriptor"/>
    <has_running_jobs>false</has_running_jobs>
    <system_type id="http://testserver/api/v1/inventory/system_types/1">Inventory</system_type>
    <generated_uuid>system-11-generated-uuid</generated_uuid>
    <ssl_server_certificate>system-11-ssl-server-certificate</ssl_server_certificate>
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <hostname/>
    <system_id>11</system_id>
    <launching_user/>
    <launch_date/>
    <system_log id="http://testserver/api/v1/inventory/systems/11/system_log"/>
    <installed_software id="http://testserver/api/v1/inventory/systems/11/installed_software"/>
    <target_system_id/>
    <jobs id="http://testserver/api/v1/inventory/systems/11/jobs">
      <queued_jobs id="http://testserver/api/v1/inventory/systems/11/job_states/1/jobs"/>
      <completed_jobs id="http://testserver/api/v1/inventory/systems/11/job_states/3/jobs"/>
      <running_jobs id="http://testserver/api/v1/inventory/systems/11/job_states/2/jobs"/>
      <failed_jobs id="http://testserver/api/v1/inventory/systems/11/job_states/4/jobs"/>
    </jobs>
    <description>System description 11</description>
    <ssl_client_certificate>system-11-ssl-client-certificate</ssl_client_certificate>
    <registration_date/>
    <has_active_jobs>false</has_active_jobs>
    <target_system_name/>
    <credentials id="http://testserver/api/v1/inventory/systems/11/credentials"/>
    <configuration id="http://testserver/api/v1/inventory/systems/11/configuration"/>
    <agent_port/>
    <project_branch_stage/>
    <out_of_date>false</out_of_date>
    <name>System name 11</name>
    <local_uuid>system-11-local-uuid</local_uuid>
    <target_system_state/>
    <project_branch/>
    <current_state id="http://testserver/api/v1/inventory/system_states/1">
      <system_state_id>1</system_state_id>
      <description>Unmanaged</description>
      <name>unmanaged</name>
      <created_date>2010-10-05T18:36:37+00:00</created_date>
    </current_state>
    <target/>
    <target_system_description/>
    <created_date>2010-12-06T22:11:00+00:00</created_date>
    <source_image/>
  </system>
</systems>
"""

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
  <installed_software id="http://testserver/api/v1/inventory/systems/3/installed_software"/>
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
  <survey id="http://testserver/api/v1/inventory/surveys/00000000-0000-4000-0000-000000000000">
    <description/>
    <name>x</name>
    <removable>False</removable>
    <uuid>00000000-0000-4000-0000-000000000000</uuid>
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
    <removable>False</removable>
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
observed_properties_alt = observed_properties_template

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

validation_report = validation_report_template
validation_report_alt = validation_report_template.replace("false","true")

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
    %(desired_properties)s
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
    desired_properties=desired_properties, 
    observed_properties=observed_properties, 
    discovered_properties=discovered_properties, 
    validation_report=validation_report,
    survey_preview=survey_preview
))

survey_input_xml_alt = (survey_input_xml_template % dict(
    system_model="",
    config_properties=config_properties_alt, 
    desired_properties=desired_properties_alt, 
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


