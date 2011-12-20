target_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target id="http://testserver/api/v1/targets/4">
  <actions>
    <action>
      <description>Configure target</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptors/configuration"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/22"/>
      <key>configure_target</key>
      <name>Configure target</name>
    </action>
    <action>
      <description>Configure user credentials for target</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptors/configure_credentials"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/20"/>
      <key>configure_target_credentials</key>
      <name>Configure user credentials for target</name>
    </action>
    <action>
      <description>Refresh images</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptors/refresh_images"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/15"/>
      <key>refresh_target_images</key>
      <name>Refresh images</name>
    </action>
    <action>
      <description>Refresh systems</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptors/refresh_systems"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/16"/>
      <key>refresh_target_systems</key>
      <name>Refresh systems</name>
    </action>
  </actions>
  <credentials_valid>false</credentials_valid>
  <description>Target Description openstack</description>
  <jobs id="http://testserver/api/v1/targets/4/jobs"/>
  <is_configured>true</is_configured>
  <name>Target Name openstack</name>
  <target_id>4</target_id>
  <target_type id="http://testserver/api/v1/target_types/3">
     <description>OpenStack</description>
     <name>openstack</name>
  </target_type>
  <target_configuration id="http://testserver/api/v1/targets/4/target_configuration"/>
  <target_user_credentials id="http://testserver/api/v1/targets/4/target_user_credentials"/>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
</target>
""".strip()

target_POST = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <name>Target Name 4</name>
  <description>Target Description</description>
  <target_type_name>vmware</target_type_name>
  <zone_name>other zone</zone_name>
</target>
""".strip()

target_PUT = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target id="http://testserver/api/v1/targets/4">
  <target_id>1</target_id>
  <name>Target 1 renamed</name>
  <target_type>
    <target_type_id>3</target_type_id>
  </target_type>
</target>
""".strip()

target_type_GET = """
<?xml version='1.0' encoding='UTF-8'?>
<target_type id="http://testserver/api/v1/target_types/3">
  <name>openstack</name>
  <description>OpenStack</description>
  <created_date>2011-09-08T17:52:39+00:00</created_date>
  <modified_date>2011-09-08T17:52:39+00:00</modified_date>
  <targets id="http://testserver/api/v1/target_types/3/targets"/>
  <descriptor_create_target id="http://testserver/api/v1/target_types/3/descriptor_create_target"/>
  <target_type_id>3</target_type_id>
</target_type>
""".strip()

target_type_by_target_id_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target_type id="http://testserver/api/v1/target_types/5">
  <created_date>2011-09-08T17:52:39+00:00</created_date>
  <description>VMware ESX/vSphere</description>
  <modified_date>2011-09-08T17:52:39+00:00</modified_date>
  <name>vmware</name>
  <target_type_id>5</target_type_id>
  <targets id="http://testserver/api/v1/target_types/5/targets"/>
  <descriptor_create_target id="http://testserver/api/v1/target_types/5/descriptor_create_target"/>
</target_type>
""".strip()

jobs_by_target_type_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<jobs count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/target_types/1/jobs/" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/target_types/1/jobs/" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-21T17:32:00.921176+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-21T17:32:00.921114+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-21T17:32:00.913831+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-21T17:32:00.913769+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
</jobs>
""".strip()

jobs_by_target_GET = \
"""
<jobs count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/targets/1/jobs/" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/targets/1/jobs/" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-21T17:31:12.245350+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-21T17:31:12.245290+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-21T17:31:12.237794+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-21T17:31:12.237733+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
</jobs>

""".strip()

all_target_jobs_GET = \
"""
<jobs count="28" next_page="http://testserver/api/v1/target_jobs/" num_pages="3" previous_page="" full_collection="http://testserver/api/v1/target_jobs/" end_index="9" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/target_jobs/" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.267860+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-22T14:47:51.267800+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.267860+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-22T14:47:51.267800+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.267860+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-22T14:47:51.267800+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.267860+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-22T14:47:51.267800+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <time_updated>2011-09-22T14:47:51.275877+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-22T14:47:51.275815+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
</jobs>
""".strip()

job_xml_with_artifacts="""
<job id="http://testserver/api/v1/jobs/uuid001">
  <created_resources>
     <image id="http://testserver/api/v1/images/9"/>
  </created_resources>
  <status_code>200</status_code>
  <job_state id="http://testserver/api/v1/job_states/3">Completed</job_state>
  <job_type id="http://testserver/api/v1/inventory/event_types/17">deploy image on target</job_type>
  <results id="http://testserver/api/v1/images/9"/>
  <created_by id="http://testserver/api/v1/users/2002">
    <user_name>ExampleDeveloper</user_name>
    <full_name>ExampleDeveloper</full_name>
  </created_by>
  <time_updated>2011-12-06T18:54:26.785093+00:00</time_updated>
  <job_description>Deploy image on target</job_description>
  <time_created>2011-12-06T18:54:26.784998+00:00</time_created>
  <status_text>Some status here</status_text>
  <job_uuid>uuid001</job_uuid>
  <systems/>
</job>
"""

job_created_system="""
<job id="http://testserver/api/v1/jobs/uuid001">
  <time_updated>2011-12-08T21:52:25.223096+00:00</time_updated>
  <status_code>200</status_code>
  <job_state id="http://testserver/api/v1/job_states/3">Completed</job_state>
  <job_type id="http://testserver/api/v1/inventory/event_types/18">launch system on target</job_type>
  <created_by id="http://testserver/api/v1/users/2002">
    <user_name>ExampleDeveloper</user_name>
    <full_name>ExampleDeveloper</full_name>
  </created_by>
  <created_resources>
    <system id="http://testserver/api/v1/inventory/systems/8"/>
  </created_resources>
  <systems/>
  <time_created>2011-12-08T21:52:25.222999+00:00</time_created>
  <status_text>Some status here</status_text>
  <job_uuid>uuid001</job_uuid>
  <job_description>Launch system on target</job_description>
</job>
"""


