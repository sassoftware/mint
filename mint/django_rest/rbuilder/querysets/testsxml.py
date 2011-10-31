#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

queryset_post_xml = """
<query_set>
  <filter_entries>
    <filter_entry>
      <field>system.name</field>
      <operator>LIKE</operator>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <name>New Query Set</name>
  <resource_type>system</resource_type>
  <description>System name has a 3 in it</description>
</query_set>
"""

# some hardcodes here, may need to be updated when installed
# querysets change, when that happens, subsitute the M
# and the N programatically, not implementing just now
queryset_put_xml = """
<query_set id="/api/v1/query_sets/15">
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>system.name</field>
      <filter_entry_id>15</filter_entry_id>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <filter_descriptor id="/api/v1/query_sets/filter_descriptor"/>
  <can_modify>true</can_modify>
  <presentation_type></presentation_type>
  <modified_date>2011-08-17T14:52:58.737001+00:00</modified_date>
  <filtered_members id="/api/v1/query_sets/15/filtered"/>
  <is_top_level>True</is_top_level>
  <tagged_date></tagged_date>
  <name>New Query Set</name>
  <chosen_members id="/api/v1/query_sets/15/chosen"/>
  <query_set_id>15</query_set_id>
  <child_members id="/api/v1/query_sets/15/child"/>
  <created_date>2011-08-17T14:52:58.736901+00:00</created_date>
  <all_members id="/api/v1/query_sets/15/all"/>
  <children>
    <query_set id="/api/v1/query_sets/5">
      <filter_entries>
        <filter_entry>
          <operator>IS_NULL</operator>
          <field>system.name</field>
          <filter_entry_id>1</filter_entry_id>
          <value>false</value>
        </filter_entry>
      </filter_entries>
      <filter_descriptor id="/api/v1/query_sets/filter_descriptor"/>
      <can_modify>false</can_modify>
      <presentation_type></presentation_type>
      <modified_date>2011-08-17T14:52:28.162448+00:00</modified_date>
      <filtered_members id="/api/v1/query_sets/5/filtered"/>
      <is_top_level>False</is_top_level>
      <tagged_date></tagged_date>
      <name>All Systems</name>
      <presentation_type>system</presentation_type>
      <chosen_members id="/api/v1/query_sets/5/chosen"/>
      <query_set_id>5</query_set_id>
      <child_members id="/api/v1/query_sets/5/child"/>
      <created_date>2011-08-17T14:52:28.162426+00:00</created_date>
      <all_members id="/api/v1/query_sets/5/all"/>
      <children/>
      <resource_type>system</resource_type>
      <description>All systems</description>
    </query_set>
  </children>
  <resource_type>system</resource_type>
  <description>System name has a 3 in it</description>
  <actions/>
</query_set>
"""

system_put_chosen_xml = """
<systems>
<system id="http://testserver/api/v1/inventory/systems/2">
</system>
</systems>
"""

queryset_with_actions = """
<query_set id="http://testserver/api/v1/query_sets/5">
  <actions>
    <action>
      <description>Refresh queryset</description>
      <descriptor id="http://testserver/api/v1/query_sets/5/descriptors/14"/>
      <enabled>true</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/14"/>
      <key>refresh_queryset</key>
      <name>refresh queryset</name>
    </action>
  </actions>
  <all_members id="http://testserver/api/v1/query_sets/5/all"/>
  <can_modify>false</can_modify>
  <child_members id="http://testserver/api/v1/query_sets/5/child"/>
  <children/>
  <chosen_members id="http://testserver/api/v1/query_sets/5/chosen"/>
  <description>All systems</description>
  <filter_descriptor id="http://testserver/api/v1/query_sets/5/filter_descriptor"/>
  <filter_entries>
    <filter_entry>
      <field>system.name</field>
      <filter_entry_id>1</filter_entry_id>
      <operator>IS_NULL</operator>
      <value>false</value>
    </filter_entry>
  </filter_entries>
  <filtered_members id="http://testserver/api/v1/query_sets/5/filtered"/>
  <grants/>
  <is_top_level>True</is_top_level>
  <name>All Systems</name>
  <presentation_type>system</presentation_type>
  <query_set_id>5</query_set_id>
  <resource_type>system</resource_type>
  <tagged_date>2011-08-29T21:44:24.358194+00:00</tagged_date>
  <universe id="http://testserver/api/v1/query_sets/5/universe"/>
  <personal_for/>
</query_set>
"""

queryset_put_xml_different = """
<query_set id="https://rbalast.eng.rpath.com/api/v1/query_sets/15" href="https://rbalast.eng.rpath.com/api/v1/query_sets/15">
        <filter_entries>
        <filter_entry>
           <field>system.name</field>
           <operator>LIKE</operator>
          <value>newterm</value>
        </filter_entry>
        </filter_entries>
        <can_modify>true</can_modify>
        <description />
        <is_top_level>true</is_top_level>
        <name>JB Test</name>
</query_set>
"""

queryset_invalidate_post_xml = """
<job>
<job_type id='https://localhost/api/v1/inventory/event_types/14'>queryset refresh</job_type>
</job>
"""

