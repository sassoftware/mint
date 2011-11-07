target_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target id="http://testserver/api/v1/targets/4">
  <actions>
    <action>
      <description>Configure user credentials for target</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptor_configure_credentials"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/20"/>
      <key>configure_target_credentials</key>
      <name>Configure user credentials for target</name>
    </action>
    <action>
      <description>Refresh images</description>
      <descriptor id="http://testserver/api/v1/targets/4/descriptor_refresh_images"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/15"/>
      <key>refresh_target_images</key>
      <name>Refresh images</name>
    </action>
  </actions>
  <credentials_valid>false</credentials_valid>
  <description>Target Description openstack</description>
  <jobs id="http://testserver/api/v1/targets/4/jobs"/>
  <name>Target Name openstack</name>
  <target_id>4</target_id>
  <target_type id="http://testserver/api/v1/target_types/3">
     <description>OpenStack</description>
     <name>openstack</name>
  </target_type>
  <target_user_credentials id="http://testserver/api/v1/targets/4/target_user_credentials"/>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
</target>
""".strip()

target_POST = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <target_id>4</target_id>
  <name>Target Name 4</name>
  <target_type>
    <type>Amazon's Crap</type>
    <description>Stuff here</description>
  </target_type>
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
<jobs count="20" next_page="http://testserver/api/v1/target_jobs/" num_pages="2" previous_page="" full_collection="http://testserver/api/v1/target_jobs/" end_index="9" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/target_jobs/" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
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
