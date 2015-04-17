#!/usr/bin/python 
inventory_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<inventory>
  <event_types id="http://testserver/api/v1/inventory/event_types"/>
  <infrastructure_systems id="http://testserver/api/v1/inventory/infrastructure_systems"/>
  <inventory_systems id="http://testserver/api/v1/inventory/inventory_systems"/>
  <job_states id="http://testserver/api/v1/inventory/job_states"/>
  <log id="http://testserver/api/v1/inventory/log"/>
  <zones id="http://testserver/api/v1/inventory/zones"/>
  <management_nodes id="http://testserver/api/v1/inventory/management_nodes"/>
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
  <event_type id="http://testserver/api/v1/inventory/event_types/28">
    <description>Create launch profile</description>
    <job_type_id>28</job_type_id>
    <name>create launch profile</name>
    <priority>105</priority>
    <resource_type>Target</resource_type>
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
    <source_image/>
    <project/>
    <current_state id="http://testserver/api/v1/inventory/system_states/3">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
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
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <network_address>
      <address>1.1.1.1</address>
      <pinned/>
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
    <registration_date/>
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
    <project/>
    <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
    <registration_date/>
    <generated_uuid>test management node guuid</generated_uuid>
    <has_active_jobs>false</has_active_jobs>
    <has_running_jobs>false</has_running_jobs>
    <network_address>
      <address>2.2.2.2</address>
      <pinned/>
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
  <project/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
    <pinned/>
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
  <project_branch_stage/>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1"/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>true</local>
  <description>test management node desc</description>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
</management_node>"""

management_node_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/v1/inventory/management_nodes/3">
  <project/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
    <pinned/>
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
  <project_branch_stage/>
  <hostname>myhostname</hostname>
  <name>test management node</name>
  <system_id>1</system_id>
  <launching_user/>
  <local>true</local>
  <description>test management node desc</description>
  <zone id="http://testserver/api/v1/inventory/zones/2"/>
  <local_uuid>test management node luuid</local_uuid>
  <project_branch/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1"/>
</management_node>"""

management_node_zone_post_response_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<management_node id="http://testserver/api/v1/inventory/management_nodes/3">
  <project/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <registration_date/>
  <generated_uuid>test management node guuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>2.2.2.2</address>
    <pinned/>
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
    <actions/>
    <project/>
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
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>rPath Update Service</name>
    <network_address>
      <address>127.0.0.1</address>
      <pinned/>
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
    <actions/>
    <project/>
    <registration_date/>
    <created_date>%s</created_date>
    <current_state id="http://testserver/api/v1/inventory/system_states/3">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>3</system_state_id>
    </current_state>
    <description>testsystemdescription</description>
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
    <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
    <name>testsystemname</name>
    <network_address>
      <address>1.1.1.1</address>
      <pinned/>
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
    <project_branch_stage/>
    <launch_date/>
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
    <current_state id="http://testserver/api/v1/inventory/system_states/2">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
    <source_image/>
  </system>
  <system id="http://testserver/api/v1/inventory/systems/2">
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
    <project_branch_stage/>
    <launch_date/>
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
    <current_state id="http://testserver/api/v1/inventory/system_states/2">
      <description>Registered</description>
      <name>registered</name>
      <system_state_id>2</system_state_id>
    </current_state>
    <created_date>%s</created_date>
    <source_image/>
  </system>
</systems>"""

system_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <actions/>
  <project/>
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <network_address>
    <address>1.1.1.1</address>
    <pinned/>
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
  <project_branch_stage/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <source_image/>
</system>"""

system_post_xml_bad_network = """
<system>
    <current_state />
    <description>exampleNewDescription</description>
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
  <project_branch_stage/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <source_image/>
</system>"""

system_delete_mgmt_interface_put_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
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
  <project_branch_stage/>
  <launch_date/>
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
  <source_image/>
</system>"""

system_post_xml_response = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <project/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>1.1.1.1</address>
    <pinned/>
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
  <target/>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
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
  <project_branch_stage/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <source_image/>
</system>"""

system_post_xml_dup2 = system_post_xml_dup.replace(
    '<name>testsystemname</name>', 
    '<name>testsystemnameChanged</name>')

system_target_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<system id="http://testserver/api/v1/inventory/systems/3">
  <actions/>
  <project/>
  <system_events id="http://testserver/api/v1/inventory/systems/3/system_events"/>
  <registration_date/>
  <generated_uuid>testsystemgenerateduuid</generated_uuid>
  <has_active_jobs>false</has_active_jobs>
  <has_running_jobs>false</has_running_jobs>
  <network_address>
    <address>1.1.1.1</address>
    <pinned/>
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
  <project/>
  %s
  <jobs id="http://testserver/api/v1/inventory/systems/3/jobs">
    <completed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/3/jobs"/>
    <failed_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/4/jobs"/>
    <queued_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/1/jobs"/>
    <running_jobs id="http://testserver/api/v1/inventory/systems/3/job_states/2/jobs"/>
  </jobs>
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
  <system_events id="http://testserver/api/v1/inventory/systems/2/system_events"/>
  <registered>True</registered>
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
  <project_branch_stage/>
  <system_id>2</system_id>
  <launching_user/>
  <launch_date/>
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
  <actions/>
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
  <project_branch_stage/>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
  <hostname/>
  <system_id>4</system_id>
  <launching_user/>
  <launch_date/>
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
  <project/>
  <target id="http://testserver/api/v1/targets/1">vsphere1.eng.rpath.com</target>
  <name>vsphere1 002</name>
  <network_address>
    <address>vsphere1-002</address>
    <pinned/>
  </network_address>
  <local_uuid/>
  <project_branch/>
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

system_post_forge_object = """<?xml version="1.0" encoding="UTF-8"?>
<system>
  <managing_zone id="http://testserver/api/v1/inventory/zones/1">Local rBuilder</managing_zone>
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
  <project_branch_stage/>
  <launch_date/>
  <description>testsystemdescription</description>
  <system_log id="http://testserver/api/v1/inventory/systems/1/system_log"/>
  <target_system_id/>
  <target_system_name/>
  <target_system_description/>
  <target_system_state/>
  <name>testsystemname</name>
  <local_uuid>testsystemlocaluuid</local_uuid>
  <project_branch/>
  <source_image/>
</system>"""
