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
<query_sets count="5" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/query_sets" end_index="4" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/query_sets;start_index=0;limit=10" start_index="0">
  <query_set id="http://testserver/api/query_sets/1">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/1/filter_descriptor"/>
    <name>All Systems</name>
    <can_modify>false</can_modify>
    <description>All Systems</description>
    <filter_entries/>
    <query_set_id>1</query_set_id>
    <all_members id="http://testserver/api/query_sets/1/all"/>
    <chosen_members id="http://testserver/api/query_sets/1/chosen"/>
    <child_members id="http://testserver/api/query_sets/1/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-All Systems-1</query_tag>
        <query_tag_id>1</query_tag_id>
        <query_set href="http://testserver/api/query_sets/1"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children>
      <query_set id="http://testserver/api/query_sets/2">
        <modified_date>2011-01-26T21:59:59+00:00</modified_date>
        <filter_descriptor id="http://testserver/api/query_sets/2/filter_descriptor"/>
        <name>Active Systems</name>
        <can_modify>false</can_modify>
        <description>Active Systems</description>
        <filter_entries>
          <filter_entry>
            <operator>EQUAL</operator>
            <field>current_state.name</field>
            <filter_entry_id>1</filter_entry_id>
            <value>responsive</value>
          </filter_entry>
        </filter_entries>
        <query_set_id>2</query_set_id>
        <all_members id="http://testserver/api/query_sets/2/all"/>
        <chosen_members id="http://testserver/api/query_sets/2/chosen"/>
        <child_members id="http://testserver/api/query_sets/2/child"/>
        <collection id="http://testserver/api/inventory/systems"/>
        <querytags>
          <query_tag>
            <query_tag>query-tag-Active Systems-2</query_tag>
            <query_tag_id>2</query_tag_id>
            <query_set href="http://testserver/api/query_sets/2"/>
            <systemtag_set/>
          </query_tag>
        </querytags>
        <created_date>2011-01-26T21:59:59+00:00</created_date>
        <is_top_level>False</is_top_level>
        <children/>
        <resource_type>system</resource_type>
        <filtered_members id="http://testserver/api/query_sets/2/filtered"/>
      </query_set>
      <query_set id="http://testserver/api/query_sets/3">
        <modified_date>2011-01-26T21:59:59+00:00</modified_date>
        <filter_descriptor id="http://testserver/api/query_sets/3/filter_descriptor"/>
        <name>Inactive Systems</name>
        <can_modify>false</can_modify>
        <description>Inactive Systems</description>
        <filter_entries>
          <filter_entry>
            <operator>IN</operator>
            <field>current_state.name</field>
            <filter_entry_id>2</filter_entry_id>
            <value>(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)</value>
          </filter_entry>
        </filter_entries>
        <query_set_id>3</query_set_id>
        <all_members id="http://testserver/api/query_sets/3/all"/>
        <chosen_members id="http://testserver/api/query_sets/3/chosen"/>
        <child_members id="http://testserver/api/query_sets/3/child"/>
        <collection id="http://testserver/api/inventory/systems"/>
        <querytags>
          <query_tag>
            <query_tag>query-tag-Inactive Systems-3</query_tag>
            <query_tag_id>3</query_tag_id>
            <query_set href="http://testserver/api/query_sets/3"/>
            <systemtag_set/>
          </query_tag>
        </querytags>
        <created_date>2011-01-26T21:59:59+00:00</created_date>
        <is_top_level>False</is_top_level>
        <children/>
        <resource_type>system</resource_type>
        <filtered_members id="http://testserver/api/query_sets/3/filtered"/>
      </query_set>
    </children>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/1/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/2">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/2/filter_descriptor"/>
    <name>Active Systems</name>
    <can_modify>false</can_modify>
    <description>Active Systems</description>
    <filter_entries>
      <filter_entry>
        <operator>EQUAL</operator>
        <field>current_state.name</field>
        <filter_entry_id>1</filter_entry_id>
        <value>responsive</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>2</query_set_id>
    <all_members id="http://testserver/api/query_sets/2/all"/>
    <chosen_members id="http://testserver/api/query_sets/2/chosen"/>
    <child_members id="http://testserver/api/query_sets/2/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Active Systems-2</query_tag>
        <query_tag_id>2</query_tag_id>
        <query_set href="http://testserver/api/query_sets/2"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>False</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/2/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/3">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/3/filter_descriptor"/>
    <name>Inactive Systems</name>
    <can_modify>false</can_modify>
    <description>Inactive Systems</description>
    <filter_entries>
      <filter_entry>
        <operator>IN</operator>
        <field>current_state.name</field>
        <filter_entry_id>2</filter_entry_id>
        <value>(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>3</query_set_id>
    <all_members id="http://testserver/api/query_sets/3/all"/>
    <chosen_members id="http://testserver/api/query_sets/3/chosen"/>
    <child_members id="http://testserver/api/query_sets/3/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Inactive Systems-3</query_tag>
        <query_tag_id>3</query_tag_id>
        <query_set href="http://testserver/api/query_sets/3"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>False</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/3/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/4">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/4/filter_descriptor"/>
    <name>Physical Systems</name>
    <can_modify>false</can_modify>
    <description>Physical Systems</description>
    <filter_entries>
      <filter_entry>
        <operator>IS_NULL</operator>
        <field>target</field>
        <filter_entry_id>3</filter_entry_id>
        <value>True</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>4</query_set_id>
    <all_members id="http://testserver/api/query_sets/4/all"/>
    <chosen_members id="http://testserver/api/query_sets/4/chosen"/>
    <child_members id="http://testserver/api/query_sets/4/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Physical Systems-4</query_tag>
        <query_tag_id>4</query_tag_id>
        <query_set href="http://testserver/api/query_sets/4"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/4/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/query_sets/5">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/5/filter_descriptor"/>
    <name>Systems named like 3</name>
    <can_modify>true</can_modify>
    <description/>
    <filter_entries>
      <filter_entry>
        <operator>LIKE</operator>
        <field>name</field>
        <filter_entry_id>4</filter_entry_id>
        <value>3</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>5</query_set_id>
    <all_members id="http://testserver/api/query_sets/5/all"/>
    <chosen_members id="http://testserver/api/query_sets/5/chosen"/>
    <child_members id="http://testserver/api/query_sets/5/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
        <query_tag>
        <query_tag>query-tag-Systems named like 3-4</query_tag>
        <query_tag_id>5</query_tag_id>
        <query_set href="http://testserver/api/query_sets/5"/>
        <systemtag_set>
          <system_tag>
            <inclusion_method/>
            <query_tag/>
            <system href="http://testserver/api/inventory/systems/4"/>
            <system_tag_id>1</system_tag_id>
          </system_tag>
        </systemtag_set>
      </query_tag>
    </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/5/filtered"/>
  </query_set>
</query_sets>
"""

query_set_xml = """\
<?xml version="1.0"?>
  <query_set id="http://testserver/api/query_sets/4">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/4/filter_descriptor"/>
    <name>Physical Systems</name>
    <can_modify>false</can_modify>
    <description>Physical Systems</description>
    <filter_entries>
      <filter_entry>
        <operator>IS_NULL</operator>
        <field>target</field>
        <filter_entry_id>3</filter_entry_id>
        <value>True</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>4</query_set_id>
    <all_members id="http://testserver/api/query_sets/4/all"/>
    <chosen_members id="http://testserver/api/query_sets/4/chosen"/>
    <child_members id="http://testserver/api/query_sets/4/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
    <querytags>
      <query_tag>
        <query_tag>query-tag-Physical Systems-4</query_tag>
        <query_tag_id>4</query_tag_id>
        <query_set href="http://testserver/api/query_sets/4"/>
        <systemtag_set/>
      </query_tag>
    </querytags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/4/filtered"/>
  </query_set>
"""

query_set_fixtured_xml = """\
<?xml version="1.0"?>
  <query_set id="http://testserver/api/query_sets/5">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/query_sets/5/filter_descriptor"/>
    <name>Systems named like 3</name>
    <can_modify>true</can_modify>
    <description/>
    <filter_entries>
      <filter_entry>
        <operator>LIKE</operator>
        <field>name</field>
        <filter_entry_id>4</filter_entry_id>
        <value>3</value>
      </filter_entry>
    </filter_entries>
    <query_set_id>5</query_set_id>
    <all_members id="http://testserver/api/query_sets/5/all"/>
    <chosen_members id="http://testserver/api/query_sets/5/chosen"/>
    <child_members id="http://testserver/api/query_sets/5/child"/>
    <collection id="http://testserver/api/inventory/systems"/>
   <querytags>
     <query_tag>
       <query_set href="http://testserver/api/query_sets/5"/>
       <query_tag>query-tag-Systems named like 3-4</query_tag>
       <query_tag_id>5</query_tag_id>
       <systemtag_set>
         <system_tag>
           <inclusion_method/>
           <query_tag/>
           <system href="http://testserver/api/inventory/systems/4"/>
           <system_tag_id>1</system_tag_id>
         </system_tag>
       </systemtag_set>
     </query_tag>
   </querytags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/query_sets/5/filtered"/>
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

query_set_child_update_xml = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/query_sets/12">
  <name>Tagged Systems 1 and 2</name>
  <children>
    <query_set id="http://127.0.0.1:8000/api/query_sets/10">
      <name>Tagged Systems 1</name>
    </query_set>
    <query_set id="http://127.0.0.1:8000/api/query_sets/11">
      <name>Tagged Systems 2</name>
    </query_set>
    <query_set id="http://127.0.0.1:8000/api/query_sets/6">
      <name>EC2 Systems</name>
    </query_set>
  </children>
</query_set>
"""
