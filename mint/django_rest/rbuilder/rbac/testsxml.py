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
<can_create>true</can_create>
</user>
"""

user_get_xml_with_roles = """
<user id="http://testserver/api/v1/users/2004">
  <blurb>something here</blurb>
  <display_email>True</display_email>
  <email>email@example.com</email>
  <full_name>ExampleIntern</full_name>
  <is_admin>false</is_admin>
  <roles id="http://testserver/api/v1/users/2004/roles"/>
  <external_auth>false</external_auth>
  <user_id>2004</user_id>
  <user_name>ExampleIntern</user_name>
  <can_create>true</can_create>
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
<role id="http://testserver/api/v1/rbac/roles/3">
   <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
   <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
   <role_id>2</role_id>
   <name>rocketsurgeon</name>
   <description></description>
</role>
"""

role_put_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/3">
   <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
   <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
   <role_id>3</role_id>
   <name>rocketsurgeon</name>
   <description></description>
   <created_by id="http://testserver/api/v1/users/1">
      <blurb/>
      <display_email/>
      <email>admin@rpath.com</email>
      <external_auth>false</external_auth>
      <full_name>Administrator</full_name>
      <is_admin>true</is_admin>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <user_id>1</user_id>
      <user_name>admin</user_name>
    </created_by>
    <modified_by id="http://testserver/api/v1/users/1">
       <blurb/>
       <display_email/>
       <email>admin@rpath.com</email>
       <external_auth>false</external_auth>
       <full_name>Administrator</full_name>
       <is_admin>true</is_admin>
       <roles id="http://testserver/api/v1/users/1/roles"/>
       <user_id>1</user_id>
       <user_name>admin</user_name>
    </modified_by>
</role>
"""

role_post_xml_input = """
<role>
   <name>rocketsurgeon</name>
   <description></description>
</role>
"""

role_post_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/6">
  <description/>
  <grants id="http://testserver/api/v1/rbac/roles/6/grants/"/>
  <name>rocketsurgeon</name>
  <role_id>6</role_id>
  <users id="http://testserver/api/v1/rbac/roles/6/users/"/>
</role>
"""

role_list_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/2">
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <role_id>1</role_id>
    <description/>
    <name>developer</name>
  <created_by id="http://testserver/api/v1/users/1">
      <blurb/>
      <display_email/>
      <email>admin@rpath.com</email>
      <external_auth>false</external_auth>
      <full_name>Administrator</full_name>
      <is_admin>true</is_admin>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <user_id>1</user_id>
      <user_name>admin</user_name>
   </created_by>
   <modified_by id="http://testserver/api/v1/users/1">
       <blurb/>
       <display_email/>
       <email>admin@rpath.com</email>
       <external_auth>false</external_auth>
       <full_name>Administrator</full_name>
       <is_admin>true</is_admin>
       <roles id="http://testserver/api/v1/users/1/roles"/>
       <user_id>1</user_id>
       <user_name>admin</user_name>
    </modified_by>
  </role>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/4">
    <users id="http://testserver/api/v1/rbac/roles/4/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/4/grants/"/>
    <role_id>3</role_id>
    <description/>
    <name>sysadmin</name>
    <created_by id="http://testserver/api/v1/users/1">
      <blurb/>
      <display_email/>
      <email>admin@rpath.com</email>
      <external_auth>false</external_auth>
      <full_name>Administrator</full_name>
      <is_admin>true</is_admin>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <user_id>1</user_id>
      <user_name>admin</user_name>
     </created_by>
     <modified_by id="http://testserver/api/v1/users/1">
       <blurb/>
       <display_email/>
       <email>admin@rpath.com</email>
       <external_auth>false</external_auth>
       <full_name>Administrator</full_name>
       <is_admin>true</is_admin>
       <roles id="http://testserver/api/v1/users/1/roles"/>
       <user_id>1</user_id>
       <user_name>admin</user_name>
    </modified_by>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
    <role_id>3</role_id>
    <description/>
    <name>intern</name>
  <created_by id="http://testserver/api/v1/users/1">
      <blurb/>
      <display_email/>
      <email>admin@rpath.com</email>
      <external_auth>false</external_auth>
      <full_name>Administrator</full_name>
      <is_admin>true</is_admin>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <user_id>1</user_id>
      <user_name>admin</user_name>
   </created_by>
   <modified_by id="http://testserver/api/v1/users/1">
       <blurb/>
       <display_email/>
       <email>admin@rpath.com</email>
       <external_auth>false</external_auth>
       <full_name>Administrator</full_name>
       <is_admin>true</is_admin>
       <roles id="http://testserver/api/v1/users/1/roles"/>
       <user_id>1</user_id>
       <user_name>admin</user_name>
    </modified_by>
   </role>
</roles>
"""

role_queryset_xml = """
<roles count="5" end_index="4" filter_by="" full_collection="http://testserver/api/v1/query_sets/11/all" id="http://testserver/api/v1/query_sets/11/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description>identity role</description>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <name>user:admin</name>
    <role_id>1</role_id>
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <name>sysadmin</name>
    <role_id>2</role_id>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
    <name>developer</name>
    <role_id>3</role_id>
    <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/4">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/4/grants/"/>
    <name>intern</name>
    <role_id>4</role_id>
    <users id="http://testserver/api/v1/rbac/roles/4/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/5">
    <description>identity role</description>
    <grants id="http://testserver/api/v1/rbac/roles/5/grants/"/>
    <name>user:testuser</name>
    <role_id>5</role_id>
    <users id="http://testserver/api/v1/rbac/roles/5/users/"/>
  </role>
</roles>
"""

role_list_xml_with_grants = """
<roles count="5" end_index="4" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description>identity role</description>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <name>user:admin</name>
    <role_id>1</role_id>
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <name>sysadmin</name>
    <role_id>2</role_id>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
    <name>developer</name>
    <role_id>3</role_id>
    <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/4">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/4/grants/"/>
    <name>intern</name>
    <role_id>4</role_id>
    <users id="http://testserver/api/v1/rbac/roles/4/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/5">
    <description>identity role</description>
    <grants id="http://testserver/api/v1/rbac/roles/5/grants/"/>
    <name>user:testuser</name>
    <role_id>5</role_id>
    <users id="http://testserver/api/v1/rbac/roles/5/users/"/>
  </role>
</roles>
"""

role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <description/>
  <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
  <name>developer</name>
  <role_id>3</role_id>
  <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
</role>
"""

permission_list_xml = """
<wrong5></wrong5>
"""

permission_list_xml_for_role = """
<grants count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/rbac/grants" id="http://testserver/api/v1/rbac/grants;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/13">
    <grant_id>13</grant_id>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/22">
      <name>datacenter</name>
    </queryset>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>sysadmin</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/14">
    <grant_id>14</grant_id>
    <permission id="http://testserver/api/v1/rbac/permissions/5">
      <description>Create Resource</description>
      <name>CreateResource</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/22">
      <name>datacenter</name>
    </queryset>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>sysadmin</name>
    </role>
  </grant>
</grants>
"""

permission_queryset_xml = """
<wrong7></wrong7>
"""

permission_get_xml = """
<grant id="http://testserver/api/v1/rbac/grants/1">
  <grant_id>1</grant_id>
  <permission id="http://testserver/api/v1/rbac/permissions/5">
    <description>Create Resource</description>
    <name>CreateResource</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/16">
    <description>resources created by user admin</description>
    <name>My Projects (admin)</name>
  </queryset>
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description>identity role</description>
    <name>user:admin</name>
  </role>
</grant>
"""

permission_post_xml_input="""
<grant>
  <permission id="http://testserver/api/v1/rbac/permissions/2">
     <description>Modify Member Resources</description>
     <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/16"/>
  <role id="http://testserver/api/v1/rbac/roles/2"/>
</grant>
"""

permission_post_xml_output="""
<grant id="http://testserver/api/v1/rbac/grants/30">
  <grant_id>30</grant_id>
  <permission id="http://testserver/api/v1/rbac/permissions/2">
    <description>Modify Member Resources</description>
    <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/16">
    <description>resources created by user admin</description>
    <name>My Projects (admin)</name>
  </queryset>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <name>sysadmin</name>
  </role>
</grant>
"""

permission_put_xml_input="""
<grant id="http://testserver/api/v1/rbac/grants/1">
  <permission id="http://testserver/api/v1/rbac/permissions/2">
    <description>Modify Member Resources</description>
    <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/18"/>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <name>intern</name>
  </role>
</grant>
"""

permission_put_xml_output="""
<grant id="http://testserver/api/v1/rbac/grants/1">
  <grant_id>1</grant_id>
  <permission id="http://testserver/api/v1/rbac/permissions/2">
    <description>Modify Member Resources</description>
    <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/18">
    <description>resources created by user admin</description>
    <name>My Systems (admin)</name>
  </queryset>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <name>intern</name>
  </role>
</grant>
"""

user_role_list_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description>identity role</description>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <name>user:admin</name>
    <role_id>1</role_id>
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <name>sysadmin</name>
    <role_id>2</role_id>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
    <name>developer</name>
    <role_id>3</role_id>
    <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
  </role>
</roles>
"""

user_role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/1">
  <description>identity role</description>
  <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
  <name>user:admin</name>
  <role_id>1</role_id>
  <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
</role>
"""

user_role_post_xml_input = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <name>intern</name>
</role>
"""

user_role_post_xml_output="""
<role id="http://testserver/api/v1/rbac/roles/3">
  <description/>
  <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
  <name>intern</name>
  <role_id>3</role_id>
  <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
</role>
"""

# NOTE -- we're not testing this ATM
# attempt to post bad XML to test our error handling
# and see what's up with it (to resolve UI bug)
user_role_post_bad_xml_input = """
<role id="https://testserver/api/v1/rbac/roles/6" href="https://testserver/api/v1/rbac/roles/6">
        <created_by id="https://testserver/api/v1/users/1" href="https://testserver/api/v1/users/1">
                <active>0</active>
                <blurb />
                <description />
                <display_email />
                <email>jmaddox@rpath.com</email>
                <full_name>Administrator</full_name>
                <is_admin>true</is_admin>
                <name>admin</name>
                <password />
                <rbacuserrole_set />
                <resource_type />
                <roles id="https://testserver/api/users/1/roles" href="https://testserver/api/users/1/roles" />
                <tags />
                <user_name>admin</user_name>
                <user_tags />
        </created_by>
        <description>All interns in the company</description>
        <grants>
                <item>
                        <errorID>0</errorID>
                        <message />
                        <name />
                        <responders />
                </item>
        </grants>
        <modified_by id="https://testserver/api/v1/users/1" href="https://testserver/api/v1/users/1" />
        <name>interns</name>
        <resource_type />
</role>
"""

user_role_get_list_xml_after_delete = """
<wrong1></wrong1>
"""

permission_type_list_xml = """
<permissions count="5" end_index="4" filter_by="" full_collection="http://testserver/api/v1/rbac/permissions" id="http://testserver/api/v1/rbac/permissions;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
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
  <permission id="http://testserver/api/v1/rbac/permissions/5">
    <description>Create Resource</description>
    <name>CreateResource</name>
    <permission_id>5</permission_id>
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

users_in_role_xml = """
<users count="1" end_index="0" filter_by="[user_roles.role.pk,EQUAL,3]" full_collection="http://testserver/api/v1/query_sets/4/all;filter_by=[user_roles.role.pk,EQUAL,3]" id="http://testserver/api/v1/query_sets/4/all;start_index=0;limit=10;filter_by=[user_roles.role.pk,EQUAL,3]" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <user id="http://testserver/api/v1/users/1">
    <blurb/>
    <can_create>true</can_create>
    <display_email/>
    <email>admin@rpath.com</email>
    <external_auth>false</external_auth>
    <is_admin>true</is_admin>
    <roles id="http://testserver/api/v1/users/1/roles"/>
    <user_id>1</user_id>
  </user>
</users>
"""

# if requesting a queryset where you don't have permission on it's contents
empty_systems_set = """
<systems count="0" end_index="0" filter_by="" full_collection="http://testserver/api/v1/query_sets/5/all" id="http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0"/>
"""



