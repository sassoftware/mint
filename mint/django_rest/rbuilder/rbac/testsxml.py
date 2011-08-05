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
