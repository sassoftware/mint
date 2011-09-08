
target_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <description>Target Description openstack</description>
  <name>Target Name openstack</name>
  <target_id>4</target_id>
  <target_type id="http://testserver/api/v1/target_types/3"/>
  <zone id="http://testserver/api/v1/inventory/zones/1"/>
</target>
""".strip()

target_POST = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <target_id>4</target_id>
  <name>Target Name 4</name>
  <target_type>
    <type>Amazon's Crap</type>
    <description>Stuff here</description>
  </target_type>
</target>
""".strip()

target_PUT = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <target_id>1</target_id>
  <name>Target 1 renamed</name>
  <target_type>
    <target_type_id>3</target_type_id>
  </target_type>
</target>
""".strip()

target_type_GET = """
<?xml version='1.0' encoding='UTF-8'?>
<target_type>
  <name>openstack</name>
  <description>OpenStack</description>
  <created_date>%s</created_date>
  <modified_date>%s</modified_date>
  <targets id="http://testserver/api/v1/target_types/3/targets"/>
  <target_type_id>3</target_type_id>
</target_type>
""".strip()

target_type_by_target_id_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target_type>
  <created_date>2011-09-08T17:52:39+00:00</created_date>
  <description>VMware ESX/vSphere</description>
  <modified_date>2011-09-08T17:52:39+00:00</modified_date>
  <name>vmware</name>
  <target_type_id>5</target_type_id>
  <targets id="http://testserver/api/v1/target_types/5/targets"/>
</target_type>
""".strip()