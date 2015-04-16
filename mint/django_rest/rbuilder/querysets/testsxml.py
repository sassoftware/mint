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

queryset_post_xml2 = """
<query_set>
  <filter_entries>
    <filter_entry>
      <field>system.name</field>
      <operator>LIKE</operator>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <name>New Query Set 2</name>
  <resource_type>system</resource_type>
  <description>New Query Set 2</description>
</query_set>
"""

# some hardcodes here, may need to be updated when installed
# querysets change, when that happens, subsitute the M
# and the N programatically, not implementing just now
queryset_put_xml = """
<query_set id="/api/v1/query_sets/20">
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>system.name</field>
      <value>3</value>
    </filter_entry>
  </filter_entries>
  <filter_descriptor id="/api/v1/query_sets/filter_descriptor"/>
  <can_modify>true</can_modify>
  <presentation_type></presentation_type>
  <modified_date>2011-08-17T14:52:58.737001+00:00</modified_date>
  <filtered_members id="/api/v1/query_sets/20/filtered"/>
  <is_top_level>True</is_top_level>
  <tagged_date></tagged_date>
  <name>New Query Set (CHANGED NAME)</name>
  <chosen_members id="/api/v1/query_sets/20/chosen"/>
  <query_set_id>16</query_set_id>
  <child_members id="/api/v1/query_sets/20/child"/>
  <created_date>2011-08-17T14:52:58.736901+00:00</created_date>
  <all_members id="/api/v1/query_sets/20/all"/>
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

remove_child_xml = """
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
"""

removed_child_xml = """
<query_set id="http://testserver/api/v1/query_sets/16">
  <filter_entries>
    <filter_entry>
      <operator>LIKE</operator>
      <field>system.name</field>
      <filter_entry_id>18</filter_entry_id>
      <value>newterm</value>
    </filter_entry>
  </filter_entries>
  <personal_for></personal_for>
  <actions/>
  <grant_matrix id="http://testserver/api/v1/query_sets/16/grant_matrix"/>
  <child_members id="http://testserver/api/v1/query_sets/16/child"/>
  <children/>
  <is_top_level>True</is_top_level>
  <can_modify>true</can_modify>
  <modified_date>2011-11-11T15:36:46.749229+00:00</modified_date>
  <modified_by id="http://testserver/api/v1/users/1">
    <user_name>admin</user_name>
    <full_name>Administrator</full_name>
  </modified_by>
  <filtered_members id="http://testserver/api/v1/query_sets/16/filtered"/>
  <query_set_id>16</query_set_id>
  <created_by id="http://testserver/api/v1/users/1">
    <user_name>admin</user_name>
    <full_name>Administrator</full_name>
  </created_by>
  <description></description>
  <presentation_type></presentation_type>
  <chosen_members id="http://testserver/api/v1/query_sets/16/chosen"/>
  <is_public>false</is_public>
  <is_static>false</is_static>
  <filter_descriptor id="http://testserver/api/v1/query_sets/16/filter_descriptor"/>
  <name>JB Test</name>
  <universe id="http://testserver/api/v1/query_sets/16/universe"/>
  <tagged_date></tagged_date>
  <all_members id="http://testserver/api/v1/query_sets/16/all"/>
  <created_date>2011-08-17T14:52:58.736901+00:00</created_date>
  <resource_type>system</resource_type>
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
  <user_create_permission>True</user_create_permission>
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
  <is_top_level>True</is_top_level>
  <name>All Systems</name>
  <presentation_type>system</presentation_type>
  <query_set_id>5</query_set_id>
  <resource_type>system</resource_type>
  <tagged_date>2011-08-29T21:44:24.358194+00:00</tagged_date>
  <universe id="http://testserver/api/v1/query_sets/5/universe"/>
  <grant_matrix id="http://testserver/api/v1/query_sets/5/grant_matrix"/>
  <personal_for/>
  <config_environments/>
</query_set>
"""

queryset_put_xml_different = """
<query_set id="https://rbalast.eng.rpath.com/api/v1/query_sets/20" href="https://rbalast.eng.rpath.com/api/v1/query_sets/20">
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

queryset_filter_descriptor_xml = """
<filter_descriptor id="http://testserver/api/v1/query_sets/5/filter_descriptor">
  <field_descriptors>
    <field_descriptor>
      <field_label>System name</field_label>
      <field_key>name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch created date</field_label>
      <field_key>project_branch.created_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch description</field_label>
      <field_key>project_branch.description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch label</field_label>
      <field_key>project_branch.label</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch modified date</field_label>
      <field_key>project_branch.modified_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch name</field_label>
      <field_key>project_branch.name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch namespace</field_label>
      <field_key>project_branch.namespace</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch platform label</field_label>
      <field_key>project_branch.platform_label</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Branch source group</field_label>
      <field_key>project_branch.source_group</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Build standard group?</field_label>
      <field_key>project_branch.build_standard_group</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image count</field_label>
      <field_key>source_image.image_count</field_key>
      <value_type>int</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image description</field_label>
      <field_key>source_image.description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image name</field_label>
      <field_key>source_image.name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image stage name</field_label>
      <field_key>source_image.stage_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image status</field_label>
      <field_key>source_image.status</field_key>
      <value_type>int</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image status message</field_label>
      <field_key>source_image.status_message</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_key>source_image.image_model</field_key>
      <field_label>Image system model</field_label>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image time created</field_label>
      <field_key>source_image.time_created</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image time updated</field_label>
      <field_key>source_image.time_updated</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image trove flavor</field_label>
      <field_key>source_image.trove_flavor</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image trove last changed</field_label>
      <field_key>source_image.trove_last_changed</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image trove name</field_label>
      <field_key>source_image.trove_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Image trove version</field_label>
      <field_key>source_image.trove_version</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project Branch ID</field_label>
      <field_key>project_branch.branch_id</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project Stage id</field_label>
      <field_key>project_branch_stage.stage_id</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project URL</field_label>
      <field_key>project.project_url</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project commit email</field_label>
      <field_key>project.commit_email</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project created date</field_label>
      <field_key>project.created_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project database</field_label>
      <field_key>project.database</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project description</field_label>
      <field_key>project.description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project disabled?</field_label>
      <field_key>project.disabled</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project domain name</field_label>
      <field_key>project.domain_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project external?</field_label>
      <field_key>project.external</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project hostname</field_label>
      <field_key>project.hostname</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project modified date</field_label>
      <field_key>project.modified_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project name</field_label>
      <field_key>project.name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project namespace</field_label>
      <field_key>project.namespace</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project repository hostname</field_label>
      <field_key>project.repository_hostname</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project short name</field_label>
      <field_key>project.short_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project type</field_label>
      <field_key>project.project_type</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Project version</field_label>
      <field_key>project.version</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Stage created date</field_label>
      <field_key>project_branch_stage.created_date</field_key>
      <value_type>datetime</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Stage label</field_label>
      <field_key>project_branch_stage.label</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Stage modified date</field_label>
      <field_key>project_branch_stage.modified_date</field_key>
      <value_type>datetime</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Stage name</field_label>
      <field_key>literal:project_branch_stage.name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Stage promotable?</field_label>
      <field_key>project_branch_stage.promotable</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System ID</field_label>
      <field_key>system_id</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System UUID</field_label>
      <field_key>generated_uuid</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System active jobs</field_label>
      <field_key>has_active_jobs</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System agent port</field_label>
      <field_key>agent_port</field_key>
      <value_type>int</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System description</field_label>
      <field_key>description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System hostname</field_label>
      <field_key>hostname</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System launch date</field_label>
      <field_key>launch_date</field_key>
      <value_type>datetime</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System local UUID</field_label>
      <field_key>local_uuid</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System modified date</field_label>
      <field_key>managementnode.modified_date</field_key>
      <value_type>datetime</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System network address (ipv4)</field_label>
      <field_key>networks.ip_address</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System network address (ipv6)</field_label>
      <field_key>networks.ipv6_address</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System registration date</field_label>
      <field_key>registration_date</field_key>
      <value_type>datetime</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System running jobs</field_label>
      <field_key>has_running_jobs</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System target system ID</field_label>
      <field_key>target_system_id</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System target system description</field_label>
      <field_key>target_system_description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System target system name</field_label>
      <field_key>target_system_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>System target system state</field_label>
      <field_key>target_system_state</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>IS_NULL</key>
          <label>Is NULL</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Target description</field_label>
      <field_key>target.description</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>Target name</field_label>
      <field_key>target.name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_key>system_type.description</field_key>
      <field_label>The description of the system type</field_label>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
         <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
      <value_type>str</value_type>
    </field_descriptor>
    <field_descriptor>
      <field_key>system_type.name</field_key>
      <field_label>The name of the system type</field_label>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options>
        <options>inventory</options>
        <options>infrastructure-management-node</options>
        <options>infrastructure-windows-build-node</options>
      </value_options>
      <value_type>str</value_type>
    </field_descriptor>
    <field_descriptor>
      <field_key>current_state.description</field_key>
      <field_label>The state description</field_label>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
      <value_type>str</value_type>
    </field_descriptor>
    <field_descriptor>
      <field_key>current_state.name</field_key>
      <field_label>The state name</field_label>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options>
        <options>unmanaged</options>
        <options>unmanaged-credentials</options>
        <options>registered</options>
        <options>responsive</options>
        <options>non-responsive-unknown</options>
        <options>non-responsive-net</options>
        <options>non-responsive-host</options>
        <options>non-responsive-shutdown</options>
        <options>non-responsive-suspended</options>
        <options>non-responsive-credentials</options>
        <options>dead</options>
        <options>mothballed</options>
      </value_options>
      <value_type>str</value_type>
    </field_descriptor>
    <field_descriptor>
      <field_label>User can create?</field_label>
      <field_key>created_by.can_create</field_key>
      <value_type>bool</value_type>
      <operator_choices>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User created date</field_label>
      <field_key>created_by.created_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User display email</field_label>
      <field_key>created_by.display_email</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User email</field_label>
      <field_key>created_by.email</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User full name</field_label>
      <field_key>created_by.full_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User id</field_label>
      <field_key>created_by.user_id</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN_OR_EQUAL</key>
          <label>Greater than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN_OR_EQUAL</key>
          <label>Less than or equal to</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>GREATER_THAN</key>
          <label>Greater than</label>
        </operator_choice>
        <operator_choice>
          <key>LESS_THAN</key>
          <label>Less than</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User last login date</field_label>
      <field_key>created_by.last_login_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User modified date</field_label>
      <field_key>created_by.modified_date</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
    <field_descriptor>
      <field_label>User name</field_label>
      <field_key>created_by.user_name</field_key>
      <value_type>str</value_type>
      <operator_choices>
        <operator_choice>
          <key>AND</key>
          <label>And</label>
        </operator_choice>
        <operator_choice>
          <key>CONTAINS</key>
          <label>Contains</label>
        </operator_choice>
        <operator_choice>
          <key>EQUAL</key>
          <label>Equal to</label>
        </operator_choice>
        <operator_choice>
          <key>IN</key>
          <label>In list</label>
        </operator_choice>
        <operator_choice>
          <key>LIKE</key>
          <label>Like</label>
        </operator_choice>
        <operator_choice>
          <key>OR</key>
          <label>Or</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_EQUAL</key>
          <label>Not equal to</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_IN</key>
          <label>Not in list</label>
        </operator_choice>
        <operator_choice>
          <key>NOT_LIKE</key>
          <label>Not like</label>
        </operator_choice>
      </operator_choices>
      <value_options/>
    </field_descriptor>
  </field_descriptors>
</filter_descriptor>
"""
