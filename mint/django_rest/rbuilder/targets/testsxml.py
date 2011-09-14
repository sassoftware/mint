
target_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target id="http://testserver/api/v1/targets/4">
  <description>Target Description openstack</description>
  <name>Target Name openstack</name>
  <target_id>4</target_id>
  <target_type id="http://testserver/api/v1/target_types/3"/>
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
<jobs count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/target_type_jobs/1/" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/target_type_jobs/1/" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <time_updated>2011-09-14T18:32:05.021478+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2011-09-14T18:32:05.021403+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid001</job_uuid>
    <job_description>System registration</job_description>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <time_updated>2011-09-14T18:32:05.028972+00:00</time_updated>
    <status_code>100</status_code>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/2">system poll</job_type>
    <time_created>2011-09-14T18:32:05.028913+00:00</time_created>
    <systems/>
    <status_text>Initializing</status_text>
    <job_uuid>rmakeuuid002</job_uuid>
    <job_description>System synchronization</job_description>
  </job>
</jobs>
""".strip()