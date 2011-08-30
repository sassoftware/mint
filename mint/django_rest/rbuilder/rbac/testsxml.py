# createa  system placeholder queryset
datacenter_xml = """
<query_set>
    <name>datacenter</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""

user_post_xml = """
<user>
<full_name>%s</full_name>
<display_email>True</display_email>
<password>password</password>
<user_name>%s</user_name>
<time_accessed>1283530322.49</time_accessed>
<time_created>1283523987.85</time_created>
<active>1</active>
<email>email@example.com</email>
<blurb>something here</blurb>
<is_admin>%s</is_admin>
</user>
"""

user_get_xml_with_roles = """
<user id="http://testserver/api/v1/users/2003">
  <blurb>something here</blurb>
  <display_email>True</display_email>
  <email>email@example.com</email>
  <full_name>ExampleIntern</full_name>
  <is_admin>false</is_admin>
  <user_roles>
    <user_role id="/api/v1/users/2003/roles/3">
      <rbac_user_role_id>3</rbac_user_role_id>
      <role id="http://testserver/api/v1/rbac/roles/3"/>
      <user id="http://testserver/api/v1/users/2003"/>
    </user_role>
  </user_roles>
  <user_groups/>
  <user_id>2003</user_id>
  <user_name>ExampleIntern</user_name>
</user>
"""

# create a lab placeholder queryset
lab_xml = """
<query_set>
    <name>lab</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""

# create a tradingfloor placeholder queryset
tradingfloor_xml = """
<query_set>
    <name>tradingfloor</name>
    <resource_type>system</resource_type>
    <filter_entries/>
</query_set>
"""


role_put_xml_input = """
<role id="http://testserver/api/v1/rbac/roles/2">
   <grants/>
   <role_id>2</role_id>
   <role_name>rocketsurgeon</role_name>
</role>
"""

role_put_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/2">
   <grants/>
   <role_id>2</role_id>
   <role_name>rocketsurgeon</role_name>
</role>
"""

role_post_xml_input = """
<role>
   <grants/>
   <role_name>rocketsurgeon</role_name>
</role>
"""

role_post_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/4">
  <grants/>
  <role_id>4</role_id>
  <role_name>rocketsurgeon</role_name>
</role>
"""

role_list_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <role_name>developer</role_name>
  </role>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <role_name>sysadmin</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <grants/>
    <role_id>2</role_id>
    <role_name>intern</role_name>
</roles>
"""

role_queryset_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/12/all" id="http://testserver/api/v1/query_sets/12/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <role_name>sysadmin</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <role_name>developer</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <grants/>
    <role_id>3</role_id>
    <role_name>intern</role_name>
  </role>
</roles>
"""

role_list_xml_with_grants = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants>
      <grant id="http://testserver/api/v1/rbac/grants/1">
        <permission>ModMembers</permission>
        <permission_id>1</permission_id>
        <queryset id="http://testserver/api/v1/query_sets/16"/>
        <role id="http://testserver/api/v1/rbac/roles/1"/>
      </grant>
    </grants>
    <role_id>1</role_id>
    <role_name>sysadmin</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants>
      <grant id="http://testserver/api/v1/rbac/grants/3">
        <permission>ModMembers</permission>
        <permission_id>3</permission_id>
        <queryset id="http://testserver/api/v1/query_sets/15"/>
        <role id="http://testserver/api/v1/rbac/roles/2"/>
      </grant>
      <grant id="http://testserver/api/v1/rbac/grants/2">
        <permission>ReadMembers</permission>
        <permission_id>2</permission_id>
        <queryset id="http://testserver/api/v1/query_sets/16"/>
        <role id="http://testserver/api/v1/rbac/roles/2"/>
      </grant>
    </grants>
    <role_id>2</role_id>
    <role_name>developer</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <grants/>
    <role_id>3</role_id>
    <role_name>intern</role_name>
  </role>
</roles>
"""

role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/2">
  <grants/>
  <role_id>2</role_id>
  <role_name>developer</role_name>
</role>
"""

permission_list_xml = """
<grants count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/grants" id="http://testserver/api/v1/rbac/grants;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/1">
    <permission_id>1</permission_id>
    <permission>ModMembers</permission>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/1"/>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/2">
    <permission>ReadMembers</permission>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <permission_id>2</permission_id>
    <role id="http://testserver/api/v1/rbac/roles/2"/>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/3">
    <permission>ModMembers</permission>
    <queryset id="http://testserver/api/v1/query_sets/15"/>
    <permission_id>3</permission_id>
    <role id="http://testserver/api/v1/rbac/roles/2"/>
  </grant>
</grants>
"""

permission_queryset_xml = """
<grants count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/13/all" id="http://testserver/api/v1/query_sets/13/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/1">
    <permission>ModMembers</permission>
    <permission_id>1</permission_id>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/1"/>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/2">
    <permission>ReadMembers</permission>
    <permission_id>2</permission_id>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/2"/>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/3">
    <permission>ModMembers</permission>
    <permission_id>3</permission_id>
    <queryset id="http://testserver/api/v1/query_sets/15"/>
    <role id="http://testserver/api/v1/rbac/roles/2"/>
  </grant>
</grants>
"""

permission_get_xml = """
<grant id="http://testserver/api/v1/rbac/grants/1">
  <permission>ModMembers</permission>
  <permission_id>1</permission_id>
  <queryset id="http://testserver/api/v1/query_sets/16"/>
  <role id="http://testserver/api/v1/rbac/roles/1"/>
</grant>
"""

permission_post_xml_input="""
<grant>
  <permission>ModMembers</permission>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <role id="http://testserver/api/v1/rbac/roles/2"/>
</grant>
"""

permission_post_xml_output="""
<grant id="http://testserver/api/v1/rbac/grants/4">
  <permission>ModMembers</permission>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <permission_id>4</permission_id>
  <role id="http://testserver/api/v1/rbac/roles/2"/>
</grant>
"""

permission_put_xml_input="""
<grant id="http://testserver/api/v1/rbac/grants/1">
  <permission>ModMembers</permission>
  <queryset id="http://testserver/api/v1/query_sets/16"/>
  <role id="http://testserver/api/v1/rbac/roles/3"/>
</grant>
"""

permission_put_xml_output="""
 <grant id="http://testserver/api/v1/rbac/grants/1">
   <permission>ModMembers</permission>
   <permission_id>1</permission_id>
   <queryset id="http://testserver/api/v1/query_sets/16"/>
   <role id="http://testserver/api/v1/rbac/roles/3"/>
 </grant>
"""

user_role_list_xml = """
<roles count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/roles" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <role_name>sysadmin</role_name>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <role_name>developer</role_name>
  </role>
</roles>
"""

user_role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/1">
  <grants/>
  <role_id>1</role_id>
  <role_name>sysadmin</role_name>
</role>
"""

user_role_post_xml_input = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <grants/>
  <role_id>3</role_id>
  <role_name>intern</role_name>
</role>
"""

user_role_post_xml_output = """
<user_role id="/api/v1/users/1/roles/3">
  <rbac_user_role_id>4</rbac_user_role_id>
  <role id="http://testserver/api/v1/rbac/roles/3"/>
  <user id="http://testserver/api/v1/users/1"/>
</user_role>
"""

user_role_get_list_xml_after_delete = """
<roles count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <role_name>developer</role_name>
  </role>
</roles>
"""

