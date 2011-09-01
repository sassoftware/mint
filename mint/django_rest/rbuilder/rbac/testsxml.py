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
  <roles id="http://testserver/api/users/2003/roles"/>
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
   <name>rocketsurgeon</name>
   <description></description>
</role>
"""

role_put_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/2">
   <grants/>
   <role_id>2</role_id>
   <name>rocketsurgeon</name>
   <description></description>
   <created_by id="http://testserver/api/v1/users/1"/>
   <modified_by id="http://testserver/api/v1/users/1"/>
</role>
"""

role_post_xml_input = """
<role>
   <grants/>
   <name>rocketsurgeon</name>
   <description></description>
</role>
"""

role_post_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/4">
  <grants/>
  <role_id>4</role_id>
  <name>rocketsurgeon</name>
  <description/>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</role>
"""

role_list_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <description/>
    <name>developer</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <description/>
    <name>sysadmin</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <grants/>
    <role_id>2</role_id>
    <description/>
    <name>intern</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
   </role>
</roles>
"""

role_queryset_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/12/all" id="http://testserver/api/v1/query_sets/12/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <description/>
    <name>sysadmin</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <description/>
    <name>developer</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <grants/>
    <role_id>3</role_id>
    <description/>
    <name>intern</name>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
</roles>
"""

role_list_xml_with_grants = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <created_by id="http://testserver/api/v1/users/1"/>
    <description/>
    <grants>
      <grant id="http://testserver/api/v1/rbac/grants/1">
        <created_by id="http://testserver/api/v1/users/1"/>
        <grant_id>1</grant_id>
        <modified_by id="http://testserver/api/v1/users/1"/>
        <permission id="http://testserver/api/v1/rbac/permissions/2">
          <description>Modify Member Resources</description>
          <name>ModMembers</name>
        </permission>
        <queryset id="http://testserver/api/v1/query_sets/16"/>
        <role id="http://testserver/api/v1/rbac/roles/1">
          <description/>
          <name>sysadmin</name>
        </role>
      </grant>
    </grants>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <name>sysadmin</name>
    <role_id>1</role_id>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <created_by id="http://testserver/api/v1/users/1"/>
    <description/>
    <grants>
      <grant id="http://testserver/api/v1/rbac/grants/3">
        <created_by id="http://testserver/api/v1/users/1"/>
        <grant_id>3</grant_id>
        <modified_by id="http://testserver/api/v1/users/1"/>
        <permission id="http://testserver/api/v1/rbac/permissions/2">
          <description>Modify Member Resources</description>
          <name>ModMembers</name>
        </permission>
        <queryset id="http://testserver/api/v1/query_sets/15"/>
        <role id="http://testserver/api/v1/rbac/roles/2">
          <description/>
          <name>developer</name>
        </role>
      </grant>
      <grant id="http://testserver/api/v1/rbac/grants/2">
        <created_by id="http://testserver/api/v1/users/1"/>
        <grant_id>2</grant_id>
        <modified_by id="http://testserver/api/v1/users/1"/>
        <permission id="http://testserver/api/v1/rbac/permissions/1">
          <description>Read Member Resources</description>
          <name>ReadMembers</name>
        </permission>
        <queryset id="http://testserver/api/v1/query_sets/16"/>
        <role id="http://testserver/api/v1/rbac/roles/2">
          <description/>
          <name>developer</name>
        </role>
      </grant>
    </grants>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <name>developer</name>
    <role_id>2</role_id>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <created_by id="http://testserver/api/v1/users/1"/>
    <description/>
    <grants/>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <name>intern</name>
    <role_id>3</role_id>
  </role>
</roles>
"""

role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/2">
  <grants/>
  <role_id>2</role_id>
  <name>developer</name>
  <description/>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</role>
"""

permission_list_xml = """
<grants count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/grants" id="http://testserver/api/v1/rbac/grants;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/1">
    <created_by id="http://testserver/api/v1/users/1"/>
    <grant_id>1</grant_id>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description/>
      <name>sysadmin</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/2">
    <created_by id="http://testserver/api/v1/users/1"/>
    <grant_id>2</grant_id>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <permission id="http://testserver/api/v1/rbac/permissions/1">
      <description>Read Member Resources</description>
      <name>ReadMembers</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>developer</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/3">
    <created_by id="http://testserver/api/v1/users/1"/>
    <grant_id>3</grant_id>
    <modified_by id="http://testserver/api/v1/users/1"/>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/15"/>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>developer</name>
    </role>
  </grant>
</grants>
"""

permission_queryset_xml = """
<grants count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/13/all" id="http://testserver/api/v1/query_sets/13/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
   <grant id="http://testserver/api/v1/rbac/grants/1">
     <created_by id="http://testserver/api/v1/users/1"/>
     <grant_id>1</grant_id>
     <modified_by id="http://testserver/api/v1/users/1"/>
     <permission id="http://testserver/api/v1/rbac/permissions/2">
       <description>Modify Member Resources</description>
       <name>ModMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/16"/>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description/>
      <name>sysadmin</name>
    </role>
   </grant>
   <grant id="http://testserver/api/v1/rbac/grants/2">
     <created_by id="http://testserver/api/v1/users/1"/>
     <grant_id>2</grant_id>
     <modified_by id="http://testserver/api/v1/users/1"/>
    <permission id="http://testserver/api/v1/rbac/permissions/1">
      <description>Read Member Resources</description>
      <name>ReadMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/16"/>
     <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>developer</name>
    </role>
   </grant>
   <grant id="http://testserver/api/v1/rbac/grants/3">
     <created_by id="http://testserver/api/v1/users/1"/>
     <grant_id>3</grant_id>
     <modified_by id="http://testserver/api/v1/users/1"/>
     <permission id="http://testserver/api/v1/rbac/permissions/2">
        <description>Modify Member Resources</description>
        <name>ModMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/15"/>
     <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>developer</name>
    </role>
   </grant>
</grants>
"""

permission_get_xml = """
<grant id="http://testserver/api/v1/rbac/grants/1">
  <permission id="http://testserver/api/v1/rbac/permissions/2">
     <description>Modify Member Resources</description>
     <name>ModMembers</name>
  </permission>
  <grant_id>1</grant_id>
  <queryset id="http://testserver/api/v1/query_sets/16"/>
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description/>
    <name>sysadmin</name>
  </role>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</grant>
"""

permission_post_xml_input="""
<grant>
  <permission id="http://testserver/api/v1/rbac/permissions/2">
     <description>Modify Member Resources</description>
     <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <role id="http://testserver/api/v1/rbac/roles/2"/>
</grant>
"""

permission_post_xml_output="""
<grant id="http://testserver/api/v1/rbac/grants/4">
  <permission id="http://testserver/api/v1/rbac/permissions/2">
     <description>Modify Member Resources</description>
     <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/14"/>
  <grant_id>4</grant_id>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <name>developer</name>
  </role>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</grant>
"""

permission_put_xml_input="""
<grant id="http://testserver/api/v1/rbac/grants/1">
  <permission id="http://testserver/api/v1/rbac/permissions/2">
    <description>Modify Member Resources</description>
    <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/16"/>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <name>intern</name>
  </role>
</grant>
"""

permission_put_xml_output="""
 <grant id="http://testserver/api/v1/rbac/grants/1">
   <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
   </permission>
   <grant_id>1</grant_id>
   <queryset id="http://testserver/api/v1/query_sets/16"/>
   <role id="http://testserver/api/v1/rbac/roles/3">
    <name>intern</name>
   </role>
   <created_by id="http://testserver/api/v1/users/1"/>
   <modified_by id="http://testserver/api/v1/users/1"/>
 </grant>
"""

user_role_list_xml = """
<roles count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/roles" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants/>
    <role_id>1</role_id>
    <name>sysadmin</name>
    <description/>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <name>developer</name>
    <description/>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
</roles>
"""

user_role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/1">
  <grants/>
  <role_id>1</role_id>
  <name>sysadmin</name>
  <description/>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</role>
"""

user_role_post_xml_input = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <grants/>
  <role_id>3</role_id>
  <name>intern</name>
</role>
"""

user_role_post_xml_output = """
<user_role id="/api/v1/users/1/roles/3">
  <rbac_user_role_id>4</rbac_user_role_id>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <name>intern</name>
  </role>  
  <user id="http://testserver/api/v1/users/1"/>
  <created_by id="http://testserver/api/v1/users/1"/>
  <modified_by id="http://testserver/api/v1/users/1"/>
</user_role>
"""

user_role_get_list_xml_after_delete = """
<roles count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants/>
    <role_id>2</role_id>
    <name>developer</name>
    <description/>
    <created_by id="http://testserver/api/v1/users/1"/>
    <modified_by id="http://testserver/api/v1/users/1"/>
  </role>
</roles>
"""

permission_type_list_xml = """
<permissions count="4" end_index="3" filter_by="" full_collection="http://testserver/api/v1/rbac/permissions" id="http://testserver/api/v1/rbac/permissions;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <permission id="http://testserver/api/v1/rbac/permissions/1">
    <description>Read Member Resources</description>
    <name>ReadMembers</name>
    <permission_id>1</permission_id>
  </permission>
  <permission id="http://testserver/api/v1/rbac/permissions/2">
    <description>Modify Member Resources</description>
    <name>ModMembers</name>
    <permission_id>2</permission_id>
  </permission>
  <permission id="http://testserver/api/v1/rbac/permissions/3">
    <description>Read Set</description>
    <name>ReadSet</name>
    <permission_id>3</permission_id>
  </permission>
  <permission id="http://testserver/api/v1/rbac/permissions/4">
    <description>Modify Set Definition</description>
    <name>ModSetDef</name>
    <permission_id>4</permission_id>
  </permission>
</permissions>
"""

permission_type_get_xml = """
<permission id="http://testserver/api/v1/rbac/permissions/2">
  <description>Modify Member Resources</description>
  <name>ModMembers</name>
  <permission_id>2</permission_id>
</permission>
"""

