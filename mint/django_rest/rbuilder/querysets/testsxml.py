#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

queryset_post_xml = """\
<query_set>
    <name>Unmanaged systems</name>
    <resource_type>system</resource_type>
    <filter_entries>
        <filter_entry field="current_state.name" operator="EQUAL" value="unmanaged"/>
    </filter_entries>
</query_set>
"""

query_sets_xml = """\
<?xml version="1.0"?>
<query_sets>
  <query_set id="http://testserver/api/query_sets/1">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/1/filter_descriptor"/>
    <name>All Systems</name>
    <filter_entries>
      <filter_entry>
        <field>name</field>
        <filter_entry_id>1</filter_entry_id>
        <operator>IS_NULL</operator>
        <value/>
      </filter_entry>
    </filter_entries>
    <query_set_id>1</query_set_id>
    <all_members id="http://testserver/api/query_sets/1/all"/>
    <chosen_members id="http://testserver/api/query_sets/1/chosen"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-All Systems-1</query_tag>
        <query_tag_id>1</query_tag_id>
        <query_set href="http://testserver/api/query_sets/1"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/1/filtered"/>
    <child_members id="http://testserver/api/query_sets/1/child"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/2">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/2/filter_descriptor"/>
    <name>Active Systems</name>
    <filter_entries>
      <filter_entry>
        <operator>EQUAL</operator>
        <field>current_state.name</field>
        <filter_entry_id>2</filter_entry_id>
        <value>responsive</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>2</query_set_id>
    <all_members id="http://testserver/api/query_sets/2/all"/>
    <chosen_members id="http://testserver/api/query_sets/2/chosen"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Active Systems-2</query_tag>
        <query_tag_id>2</query_tag_id>
        <query_set href="http://testserver/api/query_sets/2"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/2/filtered"/>
    <child_members id="http://testserver/api/query_sets/2/child"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/3">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/3/filter_descriptor"/>
    <name>Unmanaged Systems</name>
    <filter_entries>
      <filter_entry>
        <operator>EQUAL</operator>
        <field>current_state.name</field>
        <filter_entry_id>3</filter_entry_id>
        <value>unmanaged</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>3</query_set_id>
    <all_members id="http://testserver/api/query_sets/3/all"/>
    <chosen_members id="http://testserver/api/query_sets/3/chosen"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Unmanaged Systems-3</query_tag>
        <query_tag_id>3</query_tag_id>
        <query_set href="http://testserver/api/query_sets/3"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/3/filtered"/>
    <child_members id="http://testserver/api/query_sets/3/child"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/4">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/4/filter_descriptor"/>
    <name>Systems named like 3</name>
    <filter_entries>
      <filter_entry>
        <operator>LIKE</operator>
        <field>name</field>
        <filter_entry_id>4</filter_entry_id>
        <value>3</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>4</query_set_id>
    <all_members id="http://testserver/api/query_sets/4/all"/>
    <chosen_members id="http://testserver/api/query_sets/4/chosen"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Systems named like 3-4</query_tag>
        <query_tag_id>4</query_tag_id>
        <query_set href="http://testserver/api/query_sets/4"/>
        <systemtag_set>
          <system_tag>
            <inclusion_method/>
            <system_tag_id>1</system_tag_id>
            <query_tag/>
            <system href="http://testserver/api/inventory/systems/4"/>
          </system_tag>
        </systemtag_set>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/4/filtered"/>
    <child_members id="http://testserver/api/query_sets/4/child"/>
  </query_set>
</query_sets>
"""

query_set_xml = """\
<?xml version="1.0"?>
<query_set id="http://testserver/api/query_sets/4">
  <modified_date>2011-01-05T00:00:00+00:00</modified_date>
  <name>Systems named like 3</name>
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>name</field>
      <filter_entry_id>4</filter_entry_id>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <all_members id="http://testserver/api/query_sets/4/all"/>
  <chosen_members id="http://testserver/api/query_sets/4/chosen"/>
  <filter_descriptor id="http://testserver/api/query_sets/4/filter_descriptor"/>
  <query_set_id>4</query_set_id>
  <children/>
  <querytags>
    <query_tag>
      <query_tag>query-tag-Systems named like 3-4</query_tag>
      <query_tag_id>4</query_tag_id>
      <query_set href="http://testserver/api/query_sets/4"/>
      <systemtag_set>
        <system_tag>
          <inclusion_method/>
          <system_tag_id>1</system_tag_id>
          <query_tag/>
          <system href="http://testserver/api/inventory/systems/4"/>
        </system_tag>
      </systemtag_set>
    </query_tag>
  </querytags>
  <created_date>2011-01-05T00:00:00+00:00</created_date>
  <filtered_members id="http://testserver/api/query_sets/4/filtered"/>
  <child_members id="http://testserver/api/query_sets/4/child"/>
  <resource_type>system</resource_type>
</query_set>
"""

query_set_all_xml = """\
"""

query_sets_filtered_xml = """\
"""

query_sets_chosen_xml = """\
"""

systems_chosen_put_xml = """\
<?xml version="1.0"?>
<systems>
    <system id="http://testserver/api/inventory/systems/5">
        <generated_uuid>system-5-generated-uuid</generated_uuid>
        <local_uuid>system-5-local-uuid</local_uuid>
    </system>
    <system id="http://testserver/api/inventory/systems/6">
        <generated_uuid>system-6-generated-uuid</generated_uuid>
        <local_uuid>system-6-local-uuid</local_uuid>
    </system>
</systems>
"""

systems_chosen_put_xml2 = """\
<?xml version="1.0"?>
<systems>
    <system id="http://testserver/api/inventory/systems/7">
        <generated_uuid>system-7-generated-uuid</generated_uuid>
        <local_uuid>system-7-local-uuid</local_uuid>
    </system>
    <system id="http://testserver/api/inventory/systems/8">
        <generated_uuid>system-8-generated-uuid</generated_uuid>
        <local_uuid>system-8-local-uuid</local_uuid>
    </system>
</systems>
"""

query_set_update_xml = """\
<?xml version="1.0"?>
<query_set id="http://testserver/api/query_sets/4">
  <name>Systems named like 3</name>
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>name</field>
      <filter_entry_id>3</filter_entry_id>
      <value>3</value>
    </filter_entry>
    <filter_entry>
      <operator>LIKE</operator>
      <field>description</field>
      <value>3</value>
    </filter_entry>
  </filter_entries>
</query_set>
"""

