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
<user id="http://testserver/api/v1/users/2003">
  <blurb>something here</blurb>
  <display_email>True</display_email>
  <email>email@example.com</email>
  <full_name>ExampleIntern</full_name>
  <is_admin>false</is_admin>
  <roles id="http://testserver/api/v1/users/2003/roles"/>
  <external_auth>false</external_auth>
  <user_id>2003</user_id>
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
<role id="http://testserver/api/v1/rbac/roles/2">
   <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
   <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
   <role_id>2</role_id>
   <name>rocketsurgeon</name>
   <description></description>
</role>
"""

role_put_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/2">
   <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
   <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
   <role_id>2</role_id>
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
<role id="http://testserver/api/v1/rbac/roles/4">
  <grants id="http://testserver/api/v1/rbac/roles/4/grants/"/>
  <users id="http://testserver/api/v1/rbac/roles/4/users/"/>
  <role_id>4</role_id>
  <name>rocketsurgeon</name>
  <description/>
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

role_list_xml = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
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
  <role id="http://testserver/api/v1/rbac/roles/2">
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <role_id>2</role_id>
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
    <role_id>2</role_id>
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
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/11/all" id="http://testserver/api/v1/query_sets/11/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <role_id>1</role_id>
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
  <role id="http://testserver/api/v1/rbac/roles/2">
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <role_id>2</role_id>
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

role_list_xml_with_grants = """
<roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
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
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
    <name>sysadmin</name>
    <role_id>1</role_id>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/2">
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
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
    <name>developer</name>
    <role_id>2</role_id>
  </role>
  <role id="http://testserver/api/v1/rbac/roles/3">
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
    <description/>
    <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
    <name>intern</name>
    <role_id>3</role_id>
  </role>
</roles>
"""

role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/2">
  <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
  <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
  <role_id>2</role_id>
  <name>developer</name>
  <description/>
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

permission_list_xml = """
<grants count="3" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/grants" end_index="2" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/grants;start_index=0;limit=10" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/3">
    <modified_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </modified_by>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <grant_id>3</grant_id>
    <queryset id="http://testserver/api/v1/query_sets/16">
       <name>tradingfloor</name>
    </queryset>
    <created_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </created_by>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description></description>
      <name>developer</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/1">
    <modified_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </modified_by>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <grant_id>1</grant_id>
    <queryset id="http://testserver/api/v1/query_sets/18">
       <name>datacenter</name>
    </queryset>
    <created_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </created_by>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description></description>
      <name>sysadmin</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/2">
    <modified_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </modified_by>
    <permission id="http://testserver/api/v1/rbac/permissions/1">
      <description>Read Member Resources</description>
      <name>ReadMembers</name>
    </permission>
    <grant_id>2</grant_id>
    <queryset id="http://testserver/api/v1/query_sets/18">
      <name>datacenter</name>
    </queryset>
    <created_by id="http://testserver/api/v1/users/1">
      <modified_date>1283530322.49</modified_date>
      <user_id>1</user_id>
      <display_email></display_email>
      <roles id="http://testserver/api/v1/users/1/roles"/>
      <external_auth>false</external_auth>
      <is_admin>true</is_admin>
      <full_name>Administrator</full_name>
      <created_date>1283523987.85</created_date>
      <user_name>admin</user_name>
      <email>admin@rpath.com</email>
      <blurb></blurb>
    </created_by>
    <role id="http://testserver/api/v1/rbac/roles/2">
      <description></description>
      <name>developer</name>
    </role>
  </grant>
</grants>
"""

permission_list_xml_for_role = """
<grants count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/rbac/grants" id="http://testserver/api/v1/rbac/grants;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <grant id="http://testserver/api/v1/rbac/grants/1">
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
    <grant_id>1</grant_id>
    <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/18">
      <name>datacenter</name>
    </queryset>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description/>
      <name>sysadmin</name>
    </role>
  </grant>
  <grant id="http://testserver/api/v1/rbac/grants/2">
    <grant_id>2</grant_id>
    <permission id="http://testserver/api/v1/rbac/permissions/5">
      <description>Create Resource</description>
      <name>CreateResource</name>
    </permission>
    <queryset id="http://testserver/api/v1/query_sets/18">
      <name>datacenter</name>
    </queryset>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description/>
      <name>sysadmin</name>
    </role>
  </grant>
</grants>
"""

permission_queryset_xml = """
<grants count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/query_sets/12/all" id="http://testserver/api/v1/query_sets/12/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
   <grant id="http://testserver/api/v1/rbac/grants/1">
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
     <grant_id>1</grant_id>
     <permission id="http://testserver/api/v1/rbac/permissions/2">
       <description>Modify Member Resources</description>
       <name>ModMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/18">
       <name>datacenter</name>
     </queryset>
    <role id="http://testserver/api/v1/rbac/roles/1">
      <description/>
      <name>sysadmin</name>
    </role>
   </grant>
   <grant id="http://testserver/api/v1/rbac/grants/2">
     <grant_id>2</grant_id>
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
    <permission id="http://testserver/api/v1/rbac/permissions/1">
      <description>Read Member Resources</description>
      <name>ReadMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/18">
        <name>datacenter</name>
     </queryset>
     <role id="http://testserver/api/v1/rbac/roles/2">
      <description/>
      <name>developer</name>
    </role>
   </grant>
   <grant id="http://testserver/api/v1/rbac/grants/3">
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
     <grant_id>3</grant_id>
     <permission id="http://testserver/api/v1/rbac/permissions/2">
        <description>Modify Member Resources</description>
        <name>ModMembers</name>
     </permission>
     <queryset id="http://testserver/api/v1/query_sets/16">
        <name>tradingfloor</name>
     </queryset>
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
  <queryset id="http://testserver/api/v1/query_sets/18">
     <name>datacenter</name>
  </queryset>
  <role id="http://testserver/api/v1/rbac/roles/1">
    <description/>
    <name>sysadmin</name>
  </role>
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
<grant id="http://testserver/api/v1/rbac/grants/6">
  <permission id="http://testserver/api/v1/rbac/permissions/2">
     <description>Modify Member Resources</description>
     <name>ModMembers</name>
  </permission>
  <queryset id="http://testserver/api/v1/query_sets/16">
     <name>tradingfloor</name>
  </queryset>
  <grant_id>6</grant_id>
  <role id="http://testserver/api/v1/rbac/roles/2">
    <description/>
    <name>developer</name>
  </role>
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
   <permission id="http://testserver/api/v1/rbac/permissions/2">
      <description>Modify Member Resources</description>
      <name>ModMembers</name>
   </permission>
   <grant_id>1</grant_id>
   <queryset id="http://testserver/api/v1/query_sets/18">
      <name>datacenter</name>
   </queryset>
   <role id="http://testserver/api/v1/rbac/roles/3">
    <name>intern</name>
   </role>
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
 </grant>
"""

user_role_list_xml = """
<roles count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/rbac/roles" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/1">
    <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
    <role_id>1</role_id>
    <name>sysadmin</name>
    <description/>
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
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
    <role_id>2</role_id>
    <name>developer</name>
    <description/>
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

user_role_get_xml = """
<role id="http://testserver/api/v1/rbac/roles/1">
  <grants id="http://testserver/api/v1/rbac/roles/1/grants/"/>
  <users id="http://testserver/api/v1/rbac/roles/1/users/"/>
  <role_id>1</role_id>
  <name>sysadmin</name>
  <description/>
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

user_role_post_xml_input = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <name>intern</name>
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

user_role_post_xml_output = """
<role id="http://testserver/api/v1/rbac/roles/3">
  <description/>
  <grants id="http://testserver/api/v1/rbac/roles/3/grants/"/>
  <users id="http://testserver/api/v1/rbac/roles/3/users/"/>
  <name>intern</name>
  <role_id>3</role_id>
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

user_role_get_list_xml_after_delete = """
<roles count="1" end_index="0" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <role id="http://testserver/api/v1/rbac/roles/2">
    <grants id="http://testserver/api/v1/rbac/roles/2/grants/"/>
    <users id="http://testserver/api/v1/rbac/roles/2/users/"/>
    <role_id>2</role_id>
    <name>developer</name>
    <description/>
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
<users count="2" end_index="1" filter_by="" full_collection="http://testserver/api/v1/users" id="http://testserver/api/v1/users;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <user id="http://testserver/api/v1/users/2000">
    <blurb>null</blurb>
    <display_email/>
    <email>testuser@rpath.com</email>
    <full_name>Test User</full_name>
    <is_admin>false</is_admin>
    <roles id="http://testserver/api/v1/users/2000/roles"/>
    <external_auth>false</external_auth>
    <user_id>2000</user_id>
    <user_name>testuser</user_name>
    <can_create>true</can_create>
  </user>
  <user id="http://testserver/api/v1/users/1">
    <blurb/>
    <display_email/>
    <email>admin@rpath.com</email>
    <full_name>Administrator</full_name>
    <is_admin>true</is_admin>
    <roles id="http://testserver/api/v1/users/1/roles"/>
    <external_auth>false</external_auth>
    <user_id>1</user_id>
    <user_name>admin</user_name>
    <can_create>true</can_create>
  </user>
</users>
"""

# if requesting a queryset where you don't have permission on it's contents
empty_systems_set = """
<systems count="0" end_index="0" filter_by="" full_collection="http://testserver/api/v1/query_sets/5/all" id="http://testserver/api/v1/query_sets/5/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0"/>
"""



