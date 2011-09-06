
target_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <target_id>1</target_id>
  <target_name>Target Name 0</target_name>
  <target_type id="http://testserver/api/v1/target_types/1"/>
</target>
""".strip()

target_POST = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target>
  <target_id>4</target_id>
  <target_name>Target Name 4</target_name>
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
  <target_name>Target 1 renamed</target_name>
  <target_type>
    <target_type_id>3</target_type_id>
  </target_type>
</target>
""".strip()

target_types_GET = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<target_types count="3" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/target_types/" end_index="2" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/target_types/;start_index=0;limit=10" start_index="0">
  <target_type>
    <created_date></created_date>
    <description>VMWare TargetType</description>
    <modified_date></modified_date>
    <target_set>
      <target>
        <target_id>1</target_id>
        <target_name>Target Name 0</target_name>
        <target_type id="http://testserver/api/v1/target_types/1"/>
      </target>
    </target_set>
    <target_type_id>1</target_type_id>
    <type>VMWare</type>
  </target_type>
  <target_type>
    <created_date></created_date>
    <description>EC2 TargetType</description>
    <modified_date></modified_date>
    <target_set>
      <target>
        <target_id>2</target_id>
        <target_name>Target Name 1</target_name>
        <target_type id="http://testserver/api/v1/target_types/2"/>
      </target>
    </target_set>
    <target_type_id>2</target_type_id>
    <type>EC2</type>
  </target_type>
  <target_type>
    <created_date></created_date>
    <description>Moo goes the cow</description>
    <modified_date></modified_date>
    <target_set>
      <target>
        <target_id>3</target_id>
        <target_name>Target Name 2</target_name>
        <target_type id="http://testserver/api/v1/target_types/3"/>
      </target>
    </target_set>
    <target_type_id>3</target_type_id>
    <type>Heffer</type>
  </target_type>
</target_types>
""".strip()