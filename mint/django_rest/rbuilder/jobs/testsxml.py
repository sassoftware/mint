#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


jobs_xml = """\
<?xml version="1.0"?>
<jobs count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/jobs/" id="http://testserver/api/v1/jobs/" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <job_description>System registration</job_description>
    <time_updated>2010-09-16T13:36:25.939154+00:00</time_updated>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2010-09-16T13:36:25.939042+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid001</job_uuid>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <job_description>Update your system</job_description>
    <time_updated>2010-09-16T13:36:25.943043+00:00</time_updated>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/26">system update software</job_type>
    <time_created>2010-09-16T13:36:25.942952+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid002</job_uuid>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
</jobs>"""

job_xml = """\
<?xml version="1.0"?>
<job id="http://testserver/api/v1/jobs/rmakeuuid001">
  <created_resources/>
  <created_by id="http://testserver/api/v1/users/2000"/>
  <job_description>System registration</job_description>
  <time_updated>2010-09-16T13:53:18.402208+00:00</time_updated>
  <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
  <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
  <time_created>2010-09-16T13:53:18.402105+00:00</time_created>
  <systems/>
  <job_uuid>rmakeuuid001</job_uuid>
  <status_code>100</status_code>
  <status_text>Initializing</status_text>
</job>"""

job_states_xml = """\
<?xml version="1.0"?>
<job_states count="4" end_index="3" filter_by="" full_collection="http://testserver/api/v1/job_states" id="http://testserver/api/v1/job_states;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <job_state id="http://testserver/api/v1/job_states/1">
    <job_state_id>1</job_state_id>
    <jobs id="http://testserver/api/v1/job_states/1/jobs"/>
    <name>Queued</name>
  </job_state>
  <job_state id="http://testserver/api/v1/job_states/2">
    <job_state_id>2</job_state_id>
    <jobs id="http://testserver/api/v1/job_states/2/jobs"/>
    <name>Running</name>
  </job_state>
  <job_state id="http://testserver/api/v1/job_states/3">
    <job_state_id>3</job_state_id>
    <jobs id="http://testserver/api/v1/job_states/3/jobs"/>
    <name>Completed</name>
  </job_state>
  <job_state id="http://testserver/api/v1/job_states/4">
    <job_state_id>4</job_state_id>
    <jobs id="http://testserver/api/v1/job_states/4/jobs"/>
    <name>Failed</name>
  </job_state>
</job_states>"""

job_state_xml = """\
<?xml version="1.0"?>
<job_state id="http://testserver/api/v1/job_states/1">
  <job_state_id>1</job_state_id>
  <jobs id="http://testserver/api/v1/job_states/1/jobs"/>
  <name>Queued</name>
</job_state>"""

systems_jobs_xml = """\
<?xml version="1.0"?>
<jobs count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/inventory/systems/3/jobs/" id="http://testserver/api/v1/inventory/systems/3/jobs/" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <job id="http://testserver/api/v1/jobs/rmakeuuid001">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <job_description>System registration</job_description>
    <time_updated>2010-09-16T20:13:13.325788+00:00</time_updated>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/1">system registration</job_type>
    <time_created>2010-09-16T20:13:13.325686+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid001</job_uuid>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
  <job id="http://testserver/api/v1/jobs/rmakeuuid002">
    <created_resources/>
    <created_by id="http://testserver/api/v1/users/2000"/>
    <job_description>Update your system</job_description>
    <time_updated>2010-09-16T20:13:13.334487+00:00</time_updated>
    <job_state id="http://testserver/api/v1/job_states/2">Running</job_state>
    <job_type id="http://testserver/api/v1/inventory/event_types/26">system update software</job_type>
    <time_created>2010-09-16T20:13:13.334392+00:00</time_created>
    <systems/>
    <job_uuid>rmakeuuid002</job_uuid>
    <status_code>100</status_code>
    <status_text>Initializing</status_text>
  </job>
</jobs>"""
