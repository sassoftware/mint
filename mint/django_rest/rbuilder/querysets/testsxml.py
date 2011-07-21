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
<query_sets count="11" next_page="http://testserver/api/v1/query_sets;start_index=10;limit=10" num_pages="2" previous_page="" full_collection="http://testserver/api/v1/query_sets" end_index="9" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/query_sets;start_index=0;limit=10" start_index="0">
  <query_set id="http://testserver/api/v1/query_sets/1">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <name>All Systems</name>
    <can_modify>false</can_modify>
    <description>All Systems</description>
    <filter_entries/>
    <query_set_id>1</query_set_id>
    <all_members id="http://testserver/api/v1/query_sets/1/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/1/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/1/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/1/query_tags/1">
        <name>query-tag-All_Systems-1</name>
        <query_tag_id>1</query_tag_id>
        <query_set id="http://testserver/api/v1/query_sets/1"/>
      </query_tag>
    </query_tags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children>
      <query_set id="http://testserver/api/v1/query_sets/2">
        <modified_date>2011-01-26T21:59:59+00:00</modified_date>
        <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
        <all_members id="http://testserver/api/v1/query_sets/2/all"/>
        <chosen_members id="http://testserver/api/v1/query_sets/2/chosen"/>
        <child_members id="http://testserver/api/v1/query_sets/2/child"/>
        <collection id="http://testserver/api/v1/inventory/systems"/>
        <presentation_type/>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/2/query_tags/2">
            <name>query-tag-Active_Systems-2</name>
            <query_tag_id>2</query_tag_id>
            <query_set id="http://testserver/api/v1/query_sets/2"/>
          </query_tag>
        </query_tags>
        <created_date>2011-01-26T21:59:59+00:00</created_date>
        <is_top_level>False</is_top_level>
        <children/>
        <resource_type>system</resource_type>
        <filtered_members id="http://testserver/api/v1/query_sets/2/filtered"/>
      </query_set>
      <query_set id="http://testserver/api/v1/query_sets/3">
        <modified_date>2011-01-26T21:59:59+00:00</modified_date>
        <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
        <all_members id="http://testserver/api/v1/query_sets/3/all"/>
        <chosen_members id="http://testserver/api/v1/query_sets/3/chosen"/>
        <child_members id="http://testserver/api/v1/query_sets/3/child"/>
        <collection id="http://testserver/api/v1/inventory/systems"/>
        <presentation_type/>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/3/query_tags/3">
            <name>query-tag-Inactive_Systems-3</name>
            <query_tag_id>3</query_tag_id>
            <query_set id="http://testserver/api/v1/query_sets/3"/>
          </query_tag>
        </query_tags>
        <created_date>2011-01-26T21:59:59+00:00</created_date>
        <is_top_level>False</is_top_level>
        <children/>
        <resource_type>system</resource_type>
        <filtered_members id="http://testserver/api/v1/query_sets/3/filtered"/>
      </query_set>
    </children>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/1/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/2">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/2/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/2/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/2/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/2/query_tags/2">
            <name>query-tag-Active_Systems-2</name>
            <query_tag_id>2</query_tag_id>
            <query_set id="http://testserver/api/v1/query_sets/2"/>
          </query_tag>
        </query_tags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>False</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/2/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/3">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/3/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/3/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/3/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/3/query_tags/3">
            <name>query-tag-Inactive_Systems-3</name>
            <query_tag_id>3</query_tag_id>
            <query_set id="http://testserver/api/v1/query_sets/3"/>
          </query_tag>
        </query_tags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>False</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/3/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/4">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/4/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/4/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/4/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/4/query_tags/4">
        <name>query-tag-Physical_Systems-4</name>
        <query_tag_id>4</query_tag_id>
        <query_set id="http://testserver/api/v1/query_sets/4"/>
      </query_tag>
    </query_tags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/4/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/5">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/5/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/5/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/5/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/5/query_tags/5">
        <name>query-tag-Systems_named_like_3-5</name>
        <query_tag_id>5</query_tag_id>
        <query_set id="http://testserver/api/v1/query_sets/5"/>
      </query_tag>
    </query_tags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/5/filtered"/>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/6">
    <all_members id="http://testserver/api/v1/query_sets/6/all"/>
    <can_modify>false</can_modify>
    <child_members id="http://testserver/api/v1/query_sets/6/child"/>
    <children>
      <query_set id="http://testserver/api/v1/query_sets/7">
        <all_members id="http://testserver/api/v1/query_sets/7/all"/>
        <can_modify>false</can_modify>
        <child_members id="http://testserver/api/v1/query_sets/7/child"/>
        <children/>
        <chosen_members id="http://testserver/api/v1/query_sets/7/chosen"/>
        <collection id="http://testserver/api/v1/inventory/systems"/>
        <description>rPath infrastructure services for building Windows packages/images</description>
        <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
        <filter_entries>
          <filter_entry>
            <field>system_type.name</field>
            <filter_entry_id>6</filter_entry_id>
            <operator>EQUAL</operator>
            <value>infrastructure-windows-build-node</value>
          </filter_entry>
        </filter_entries>
        <filtered_members id="http://testserver/api/v1/query_sets/7/filtered"/>
        <is_top_level>False</is_top_level>
        <name>rPath Windows Build Services</name>
        <presentation_type/>
        <query_set_id>7</query_set_id>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/7/query_tags/7">
            <name>query-tag-Windows_Build_Services-7</name>
            <query_set id="http://testserver/api/v1/query_sets/7"/>
            <query_tag_id>7</query_tag_id>
          </query_tag>
        </query_tags>
        <resource_type>system</resource_type>
      </query_set>
      <query_set id="http://testserver/api/v1/query_sets/8">
        <all_members id="http://testserver/api/v1/query_sets/8/all"/>
        <can_modify>false</can_modify>
        <child_members id="http://testserver/api/v1/query_sets/8/child"/>
        <children/>
        <chosen_members id="http://testserver/api/v1/query_sets/8/chosen"/>
        <collection id="http://testserver/api/v1/inventory/systems"/>
        <description>rPath infrastructure services for managing systems</description>
        <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
        <filter_entries>
          <filter_entry>
            <field>system_type.name</field>
            <filter_entry_id>7</filter_entry_id>
            <operator>EQUAL</operator>
            <value>infrastructure-management-node</value>
          </filter_entry>
        </filter_entries>
        <filtered_members id="http://testserver/api/v1/query_sets/8/filtered"/>
        <is_top_level>False</is_top_level>
        <name>rPath Update Services</name>
        <presentation_type/>
        <query_set_id>8</query_set_id>
        <query_tags>
          <query_tag id="http://testserver/api/v1/query_sets/8/query_tags/8">
            <name>query-tag-Update_Services-8</name>
            <query_set id="http://testserver/api/v1/query_sets/8"/>
            <query_tag_id>8</query_tag_id>
          </query_tag>
        </query_tags>
        <resource_type>system</resource_type>
      </query_set>
    </children>
    <chosen_members id="http://testserver/api/v1/query_sets/6/chosen"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <description>Systems that make up the rPath infrastructure</description>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <filter_entries>
      <filter_entry>
        <field>system_type.infrastructure</field>
        <filter_entry_id>5</filter_entry_id>
        <operator>EQUAL</operator>
        <value>true</value>
      </filter_entry>
    </filter_entries>
    <filtered_members id="http://testserver/api/v1/query_sets/6/filtered"/>
    <is_top_level>True</is_top_level>
    <name>Infrastructure Systems</name>
    <presentation_type/>
    <query_set_id>6</query_set_id>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/6/query_tags/6">
        <name>query-tag-Infrastructure_Systems-6</name>
        <query_set id="http://testserver/api/v1/query_sets/6"/>
        <query_tag_id>6</query_tag_id>
      </query_tag>
    </query_tags>
    <resource_type>system</resource_type>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/7">
    <all_members id="http://testserver/api/v1/query_sets/7/all"/>
    <can_modify>false</can_modify>
    <child_members id="http://testserver/api/v1/query_sets/7/child"/>
    <children/>
    <chosen_members id="http://testserver/api/v1/query_sets/7/chosen"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <description>rPath infrastructure services for building Windows packages/images</description>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <filter_entries>
      <filter_entry>
        <field>system_type.name</field>
        <filter_entry_id>6</filter_entry_id>
        <operator>EQUAL</operator>
        <value>infrastructure-windows-build-node</value>
      </filter_entry>
    </filter_entries>
    <filtered_members id="http://testserver/api/v1/query_sets/7/filtered"/>
    <is_top_level>False</is_top_level>
    <name>rPath Windows Build Services</name>
    <presentation_type/>
    <query_set_id>7</query_set_id>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/7/query_tags/7">
        <name>query-tag-Windows_Build_Services-7</name>
        <query_set id="http://testserver/api/v1/query_sets/7"/>
        <query_tag_id>7</query_tag_id>
      </query_tag>
    </query_tags>
    <resource_type>system</resource_type>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/8">
    <all_members id="http://testserver/api/v1/query_sets/8/all"/>
    <can_modify>false</can_modify>
    <child_members id="http://testserver/api/v1/query_sets/8/child"/>
    <children/>
    <chosen_members id="http://testserver/api/v1/query_sets/8/chosen"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <description>rPath infrastructure services for managing systems</description>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <filter_entries>
      <filter_entry>
        <field>system_type.name</field>
        <filter_entry_id>7</filter_entry_id>
        <operator>EQUAL</operator>
        <value>infrastructure-management-node</value>
      </filter_entry>
    </filter_entries>
    <filtered_members id="http://testserver/api/v1/query_sets/8/filtered"/>
    <is_top_level>False</is_top_level>
    <name>rPath Update Services</name>
    <presentation_type/>
    <query_set_id>8</query_set_id>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/8/query_tags/8">
        <name>query-tag-Update_Services-8</name>
        <query_set id="http://testserver/api/v1/query_sets/8"/>
        <query_tag_id>8</query_tag_id>
      </query_tag>
    </query_tags>
    <resource_type>system</resource_type>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/9">
    <all_members id="http://testserver/api/v1/query_sets/9/all"/>
    <can_modify>false</can_modify>
    <child_members id="http://testserver/api/v1/query_sets/9/child"/>
    <children/>
    <chosen_members id="http://testserver/api/v1/query_sets/9/chosen"/>
    <collection id="http://testserver/api/v1/project_branch_stages"/>
    <description>All project stages</description>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <filter_entries/>
    <filtered_members id="http://testserver/api/v1/query_sets/9/filtered"/>
    <is_top_level>True</is_top_level>
    <name>All Project Stages</name>
    <presentation_type>project</presentation_type>
    <query_set_id>9</query_set_id>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/9/query_tags/9">
        <name>query-tag-All_Project_Branch_Stages-13</name>
        <query_set id="http://testserver/api/v1/query_sets/9"/>
        <query_tag_id>9</query_tag_id>
      </query_tag>
    </query_tags>
    <resource_type>project_branch_stage</resource_type>
  </query_set>
  <query_set id="http://testserver/api/v1/query_sets/10">
    <all_members id="http://testserver/api/v1/query_sets/10/all"/>
    <can_modify>false</can_modify>
    <child_members id="http://testserver/api/v1/query_sets/10/child"/>
    <children/>
    <chosen_members id="http://testserver/api/v1/query_sets/10/chosen"/>
    <collection id="http://testserver/api/v1/project_branch_stages"/>
    <description>All platforms</description>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
    <filter_entries/>
    <filtered_members id="http://testserver/api/v1/query_sets/10/filtered"/>
    <is_top_level>True</is_top_level>
    <name>All Platforms</name>
    <presentation_type>platform</presentation_type>
    <query_set_id>10</query_set_id>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/10/query_tags/10">
        <name>query-tag-All_Platforms-12</name>
        <query_set id="http://testserver/api/v1/query_sets/10"/>
        <query_tag_id>10</query_tag_id>
      </query_tag>
    </query_tags>
    <resource_type>project_branch_stage</resource_type>
  </query_set>
</query_sets>
"""

query_set_xml = """\
<?xml version="1.0"?>
  <query_set id="http://testserver/api/v1/query_sets/4">
    <modified_date>2011-01-26T21:59:59+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/4/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/4/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/4/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
    <presentation_type/>
    <query_tags>
      <query_tag id="http://testserver/api/v1/query_sets/4/query_tags/4">
        <name>query-tag-Physical_Systems-4</name>
        <query_tag_id>4</query_tag_id>
        <query_set id="http://testserver/api/v1/query_sets/4"/>
      </query_tag>
    </query_tags>
    <created_date>2011-01-26T21:59:59+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members id="http://testserver/api/v1/query_sets/4/filtered"/>
  </query_set>
"""

query_set_fixtured_xml = """\
<?xml version="1.0"?>
  <query_set id="http://testserver/api/v1/query_sets/5">
    <modified_date>2011-01-05T00:00:00+00:00</modified_date>
    <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
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
    <all_members id="http://testserver/api/v1/query_sets/5/all"/>
    <chosen_members id="http://testserver/api/v1/query_sets/5/chosen"/>
    <child_members id="http://testserver/api/v1/query_sets/5/child"/>
    <collection id="http://testserver/api/v1/inventory/systems"/>
   <query_tags>
     <query_tag id="http://testserver/api/v1/query_sets/5/query_tags/5">
       <query_set id="http://testserver/api/v1/query_sets/5"/>
       <name>query-tag-Systems_named_like_3-5</name>
       <query_tag_id>5</query_tag_id>
     </query_tag>
   </query_tags>
    <created_date>2011-01-05T00:00:00+00:00</created_date>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <presentation_type/>
    <filtered_members id="http://testserver/api/v1/query_sets/5/filtered"/>
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
    <system id="http://testserver/api/v1/inventory/systems/5">
        <generated_uuid>system-5-generated-uuid</generated_uuid>
        <local_uuid>system-5-local-uuid</local_uuid>
    </system>
    <system id="http://testserver/api/v1/inventory/systems/6">
        <generated_uuid>system-6-generated-uuid</generated_uuid>
        <local_uuid>system-6-local-uuid</local_uuid>
    </system>
</systems>
"""

systems_chosen_put_xml2 = """\
<?xml version="1.0"?>
<systems>
    <system id="http://testserver/api/v1/inventory/systems/7">
        <generated_uuid>system-7-generated-uuid</generated_uuid>
        <local_uuid>system-7-local-uuid</local_uuid>
    </system>
    <system id="http://testserver/api/v1/inventory/systems/8">
        <generated_uuid>system-8-generated-uuid</generated_uuid>
        <local_uuid>system-8-local-uuid</local_uuid>
    </system>
</systems>
"""

systems_chosen_post_xml = """\
<?xml version="1.0"?>
<system id="http://testserver/api/v1/inventory/systems/7">
    <generated_uuid>system-7-generated-uuid</generated_uuid>
    <local_uuid>system-7-local-uuid</local_uuid>
</system>
"""

systems_chosen_post_xml2 = """\
<?xml version="1.0"?>
<system id="http://testserver/api/v1/inventory/systems/8">
    <generated_uuid>system-8-generated-uuid</generated_uuid>
    <local_uuid>system-8-local-uuid</local_uuid>
</system>
"""

systems_chosen_post_xml3 = """\
<?xml version="1.0"?>
<system id="http://testserver/api/v1/inventory/systems/9"/>
"""

query_set_update_xml = """\
<?xml version="1.0"?>
<query_set id="http://testserver/api/v1/query_sets/5">
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
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/12">
  <name>Tagged Systems 1 and 2</name>
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/10">
      <name>Tagged Systems 1</name>
    </query_set>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/11">
      <name>Tagged Systems 2</name>
    </query_set>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/6">
      <name>EC2 Systems</name>
    </query_set>
  </children>
</query_set>
"""

query_set_child_update_xml2 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/12">
  <name>Tagged Systems 1 and 2</name>
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/10"/>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/11"/>
  </children>
</query_set>
"""

query_set_child_update_xml3 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/12">
  <name>Tagged Systems 1 and 2</name>
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/10"/>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/11"/>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/6"/>
  </children>
</query_set>
"""

query_set_child_update_xml4 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/12">
  <name>Tagged Systems 1 and 2</name>
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/10"/>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/11"/>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/12"/>
  </children>
</query_set>
"""

query_set_child_update_xml5 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/10">
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/12"/>
  </children>
</query_set>
"""

query_set_child_update_xml6 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/10">
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/11"/>
  </children>
</query_set>
"""

query_set_child_update_xml7 = """\
<?xml version="1.0"?>
<query_set id="http://127.0.0.1:8000/api/v1/query_sets/11">
  <children>
    <query_set id="http://127.0.0.1:8000/api/v1/query_sets/12"/>
  </children>
</query_set>
"""

system_4_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<system id="http://127.0.0.1:8000/api/v1/inventory/systems/4">
  <generated_uuid>system-4-generated-uuid</generated_uuid>
  <system_tags/>
  <local_uuid>system-4-local-uuid</local_uuid>
</system>
"""

system_7_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<system id="http://127.0.0.1:8000/api/v1/inventory/systems/7">
  <generated_uuid>system-7-generated-uuid</generated_uuid>
  <local_uuid>system-7-local-uuid</local_uuid>
  <system_tags>
    <system_tag id="http://127.0.0.1:8000/api/v1/inventory/systems/7/system_tags/2">
      <query_tag id="http://127.0.0.1:8000/api/v1/query_sets/5/query_tags/5">query-tag-Systems_named_like_3-5</query_tag>
      <inclusion_method>
        <name>chosen</name>
      </inclusion_method>
      <system id="http://127.0.0.1:8000/api/v1/inventory/systems/7"/>
    </system_tag>
  </system_tags>
</system>
"""

queryset_post_xml2 = """\
<?xml version="1.0"?>
  <query_set>
    <modified_date/>
    <filter_descriptor/>
    <name>A new query set</name>
    <can_modify>true</can_modify>
    <description>New query set for physical systems</description>
    <filter_entries>
      <filter_entry>
        <operator>IS_NULL</operator>
        <field>target</field>
        <value>True</value>
      </filter_entry>
    </filter_entries>
    <query_set_id/>
    <all_members/>
    <chosen_members/>
    <child_members/>
    <collection/>
    <query_tags/>
    <created_date/>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members/>
  </query_set>
"""

queryset_post_response_xml2 = """\
<query_set id="http://testserver/api/v1/query_sets/12">
  <filter_entries>
    <filter_entry>
      <operator>IS_NULL</operator>
      <field>target</field>
      <filter_entry_id>3</filter_entry_id>
      <value>True</value>
    </filter_entry>
  </filter_entries>
  <filter_descriptor id="http://testserver/api/v1/query_sets/filter_descriptor"/>
  <can_modify>true</can_modify>
  <modified_date>2011-03-16T21:33:47.055412+00:00</modified_date>
  <filtered_members id="http://testserver/api/v1/query_sets/12/filtered"/>
  <description>New query set for physical systems</description>
  <child_members id="http://testserver/api/v1/query_sets/12/child"/>
  <presentation_type/>
  <query_tags>
    <query_tag id="http://testserver/api/v1/query_sets/12/query_tags/12">
      <query_tag_id>12</query_tag_id>
      <query_set id="http://testserver/api/v1/query_sets/12"/>
      <name>query-tag-A_new_query_set-12</name>
    </query_tag>
  </query_tags>
  <chosen_members id="http://testserver/api/v1/query_sets/12/chosen"/>
  <query_set_id>12</query_set_id>
  <collection id="http://testserver/api/v1/inventory/systems"/>
  <is_top_level>False</is_top_level>
  <created_date>2011-03-16T21:33:47.055325+00:00</created_date>
  <all_members id="http://testserver/api/v1/query_sets/12/all"/>
  <children/>
  <resource_type>system</resource_type>
  <name>A new query set</name>
</query_set>
"""

queryset_post_xml3 = """\
<?xml version="1.0"?>
  <query_set>
    <modified_date/>
    <filter_descriptor/>
    <name>A new query set</name>
    <can_modify>true</can_modify>
    <description>New query set for virtual systems</description>
    <filter_entries>
      <filter_entry>
        <operator>IS_NULL</operator>
        <field>target</field>
        <value>False</value>
      </filter_entry>
    </filter_entries>
    <query_set_id/>
    <all_members/>
    <chosen_members/>
    <child_members/>
    <collection/>
    <query_tags/>
    <created_date/>
    <is_top_level>True</is_top_level>
    <children/>
    <resource_type>system</resource_type>
    <filtered_members/>
  </query_set>
"""
