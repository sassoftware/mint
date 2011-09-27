images_get_xml = """
<images count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/images" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/images;start_index=0;limit=10" start_index="0">
  <image id="http://testserver/api/v1/images/1">
    <name>placeholder</name>
  </image>
  <image id="http://testserver/api/v1/images/2">
    <name>placeholder</name>
  </image>
</images>
"""

image_get_xml = """
<image id="http://testserver/api/v1/images/1">
    <name>placeholder</name>
</image>
"""

build_file_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<build_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title></title>
  <file_id>1</file_id>
  <build/>
  <size>0</size>
</build_file>
""".strip()