role_put_xml_input = """
<rbac_role id="http://testserver/api/v1/rbac/roles/rocket%20surgeon">
   <role_id>rocket surgeon</role_id>
</rbac_role>
"""

# TODO, ID should come back on this element
role_put_xml_output = """
<rbac_role>
   <role_id>rocket surgeon</role_id>
</rbac_role>
"""

role_list_xml = """
<rbac_roles count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/roles" id="http://testserver/api/v1/rbac/roles;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_role id="http://testserver/api/v1/rbac/roles/sysadmin">
    <role_id>sysadmin</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/developer">
    <role_id>developer</role_id>
  </rbac_role>
  <rbac_role id="http://testserver/api/v1/rbac/roles/intern">
    <role_id>intern</role_id>
  </rbac_role>
</rbac_roles>
"""

role_get_xml = """
<rbac_role id="http://testserver/api/v1/rbac/roles/developer">
  <role_id>developer</role_id>
</rbac_role>
"""

context_put_xml_input = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter2">
   <context_id>datacenter2</context_id>
</rbac_context>
"""

context_put_xml_output = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter2">
   <context_id>datacenter2</context_id>
</rbac_context>
"""

context_list_xml = """
<rbac_contexts count="3" end_index="2" filter_by="" full_collection="http://testserver/api/v1/rbac/contexts" id="http://testserver/api/v1/rbac/contexts;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0">
  <rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter">
    <context_id>datacenter</context_id>
  </rbac_context>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/lab">
    <context_id>lab</context_id>
  </rbac_context>
  <rbac_context id="http://testserver/api/v1/rbac/contexts/tradingfloor">
    <context_id>tradingfloor</context_id>
  </rbac_context>
</rbac_contexts>
"""

context_get_xml = """
<rbac_context id="http://testserver/api/v1/rbac/contexts/datacenter">
  <context_id>datacenter</context_id>
</rbac_context>
"""

