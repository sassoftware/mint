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
# querysets change, when that happens, subsitute the 12
# and the 5 programatically, not implementing just now
queryset_put_xml = """
<query_set id="/api/v1/query_sets/12">
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>system.name</field>
      <filter_entry_id>12</filter_entry_id>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <filter_descriptor id="/api/v1/query_sets/filter_descriptor"/>
  <can_modify>true</can_modify>
  <presentation_type></presentation_type>
  <modified_date>2011-08-17T14:52:58.737001+00:00</modified_date>
  <filtered_members id="/api/v1/query_sets/12/filtered"/>
  <is_top_level>True</is_top_level>
  <tagged_date></tagged_date>
  <query_tags>
    <query_tag id="/api/v1/query_sets/12/query_tags/12">
      <query_tag_id>12</query_tag_id>
      <query_set id="/api/v1/query_sets/12"/>
      <name>query-tag-New_Query_Set-12</name>
    </query_tag>
  </query_tags>
  <name>New Query Set</name>
  <chosen_members id="/api/v1/query_sets/12/chosen"/>
  <query_set_id>12</query_set_id>
  <child_members id="/api/v1/query_sets/12/child"/>
  <created_date>2011-08-17T14:52:58.736901+00:00</created_date>
  <all_members id="/api/v1/query_sets/12/all"/>
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
      <query_tags>
        <query_tag id="/api/v1/query_sets/5/query_tags/1">
          <query_tag_id>1</query_tag_id>
          <query_set id="/api/v1/query_sets/5"/>
          <name>query-tag-All_Systems-15</name>
        </query_tag>
      </query_tags>
      <name>All Systems</name>
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
</query_set>
"""

