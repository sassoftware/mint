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
    <name>All Systems</name>
    <filter_entries/>
    <allMembers>http://testserver/api/query_sets/1/all</allMembers>
    <chosenMembers>http://testserver/api/query_sets/1/chosen</chosenMembers>
    <query_set_id>1</query_set_id>
    <children/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-All Systems-1</query_tag>
        <query_tag_id>1</query_tag_id>
        <query_set href="http://testserver/api/query_sets/1"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <filteredMembers>http://testserver/api/query_sets/1/filtered</filteredMembers>
    <resource_type>system</resource_type>
  </query_set>
  <query_set id="http://testserver/api/query_sets/2">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <name>Systems named like 3</name>
    <filter_entries>
      <filter_entry>
        <operator>LIKE</operator>
        <field>name</field>
        <filter_entry_id>1</filter_entry_id>
        <value>3</value>
      </filter_entry>
    </filter_entries>
    <allMembers>http://testserver/api/query_sets/2/all</allMembers>
    <chosenMembers>http://testserver/api/query_sets/2/chosen</chosenMembers>
    <query_set_id>2</query_set_id>
    <children/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Systems named like 3-2</query_tag>
        <query_tag_id>2</query_tag_id>
        <query_set href="http://testserver/api/query_sets/2"/>
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
    <filteredMembers>http://testserver/api/query_sets/2/filtered</filteredMembers>
    <resource_type>system</resource_type>
  </query_set>
</query_sets>
"""

query_set_xml = """\
<?xml version="1.0"?>
<query_set id="http://testserver/api/query_sets/2">
  <modified_date>2011-01-05T00:00:00+00:00</modified_date>
  <name>Systems named like 3</name>
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>name</field>
      <filter_entry_id>1</filter_entry_id>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <allMembers>http://testserver/api/query_sets/2/all</allMembers>
  <chosenMembers>http://testserver/api/query_sets/2/chosen</chosenMembers>
  <query_set_id>2</query_set_id>
  <children/>
  <querytags>
    <query_tag>
      <query_tag>query-tag-Systems named like 3-2</query_tag>
      <query_tag_id>2</query_tag_id>
      <query_set href="http://testserver/api/query_sets/2"/>
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
  <filteredMembers>http://testserver/api/query_sets/2/filtered</filteredMembers>
  <resource_type>system</resource_type>
</query_set>
"""

query_set_all_xml = """\
"""

query_sets_filtered_xml = """\
"""

query_sets_chosen_xml = """\
"""

