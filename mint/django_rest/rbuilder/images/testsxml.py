images_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<images count="3" next_page="" num_pages="1" previous_page="" full_collection="" end_index="2" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <image>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trove_flavor>is: x86</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <systems/>
    <status_message></status_message>
    <trove_name>troveName0</trove_name>
    <build_count>1</build_count>
    <status>-1</status>
    <stage_name>stage0</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-0</description>
    <image_id>1</image_id>
    <time_created></time_created>
    <build_type>10</build_type>
    <time_updated></time_updated>
    <name>image-0</name>
    <trove_version>foo@test:1/1-0-1</trove_version>
    <project id="http://testserver/api/v1/projects/foo0">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo0</short_name>
      <name>foo0</name>
    </project>
    <output_trove></output_trove>
    <release/>
    <job_uuid>1</job_uuid>
  </image>
  <image>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trove_flavor>is: x86</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <systems/>
    <status_message></status_message>
    <trove_name>troveName1</trove_name>
    <build_count>1</build_count>
    <status>-1</status>
    <stage_name>stage1</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo1/project_branches/foo1.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-1</description>
    <image_id>2</image_id>
    <time_created></time_created>
    <build_type>10</build_type>
    <time_updated></time_updated>
    <name>image-1</name>
    <trove_version>foo@test:1/1-1-1</trove_version>
    <project id="http://testserver/api/v1/projects/foo1">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo1</short_name>
      <name>foo1</name>
    </project>
    <output_trove></output_trove>
    <release/>
    <job_uuid>1</job_uuid>
  </image>
  <image>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trove_flavor>is: x86</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <systems/>
    <status_message></status_message>
    <trove_name>troveName2</trove_name>
    <build_count>1</build_count>
    <status>-1</status>
    <stage_name>stage2</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo2/project_branches/foo2.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-2</description>
    <image_id>3</image_id>
    <time_created></time_created>
    <build_type>10</build_type>
    <time_updated></time_updated>
    <name>image-2</name>
    <trove_version>foo@test:1/1-2-1</trove_version>
    <project id="http://testserver/api/v1/projects/foo2">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo2</short_name>
      <name>foo2</name>
    </project>
    <output_trove></output_trove>
    <release/>
    <job_uuid>1</job_uuid>
  </image>
</images>
"""

image_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<image>
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trove_flavor>is: x86</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <systems/>
  <status_message></status_message>
  <trove_name>troveName0</trove_name>
  <build_count>1</build_count>
  <status>-1</status>
  <stage_name>stage0</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-0</description>
  <image_id>1</image_id>
  <time_created></time_created>
  <build_type>10</build_type>
  <time_updated></time_updated>
  <name>image-0</name>
  <trove_version>foo@test:1/1-0-1</trove_version>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <output_trove></output_trove>
  <release/>
  <job_uuid>1</job_uuid>
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

image_post_xml = """
<image>
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trove_flavor>is: x86</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <systems/>
  <status_message></status_message>
  <trove_name>troveName20</trove_name>
  <build_count>1</build_count>
  <status>-1</status>
  <stage_name>stage20</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-20</description>
  <time_created></time_created>
  <build_type>10</build_type>
  <time_updated></time_updated>
  <name>image-20</name>
  <trove_version>foo0@test:1/1-0-1</trove_version>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <output_trove></output_trove>
  <release/>
  <job_uuid>2</job_uuid>
</image>
"""

image_put_xml = """
<image>
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trove_flavor>is: x86</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <systems/>
  <status_message></status_message>
  <trove_name>troveName20-Changed</trove_name>
  <build_count>1</build_count>
  <status>-1</status>
  <stage_name>stage20</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-20</description>
  <time_created></time_created>
  <build_type>10</build_type>
  <time_updated></time_updated>
  <name>image-20</name>
  <trove_version>newfoo@test:1/1-0-1</trove_version>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <output_trove></output_trove>
  <release/>
  <job_uuid>2</job_uuid>
</image>
"""

build_file_post_xml = \
"""
<build_file>
    <build>
      <trove_last_changed></trove_last_changed>
      <updated_by id="http://testserver/api/v1/users/2002"/>
      <trove_flavor>is: x86</trove_flavor>
      <created_by id="http://testserver/api/v1/users/2001"/>
      <systems/>
      <status_message></status_message>
      <trove_name>troveName20-Changed</trove_name>
      <build_count>1</build_count>
      <status>-1</status>
      <stage_name>stage20</stage_name>
      <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
        <name>trunk</name>
      </project_branch>
      <description>image-20</description>
      <time_created></time_created>
      <build_type>10</build_type>
      <time_updated></time_updated>
      <name>image-20</name>
      <trove_version>newfoo@test:1/1-0-1</trove_version>
      <project id="http://testserver/api/v1/projects/foo0">
        <domain_name>eng.rpath.com</domain_name>
        <short_name>foo0</short_name>
        <name>foo0</name>
      </project>
      <output_trove></output_trove>
      <release/>
      <job_uuid>2</job_uuid>
    </build>
    <sha1>0</sha1>
    <idx>0</idx>
    <title>HelloWorld</title>
    <size>0</size>
</build_file>
""".strip()

build_files_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<build_files count="1" next_page="" num_pages="1" previous_page="" full_collection="" end_index="0" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <build_file>
    <sha1>0</sha1>
    <idx>0</idx>
    <title></title>
    <file_id>1</file_id>
    <build/>
    <size>0</size>
  </build_file>
</build_files>
""".strip()

build_file_posted_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<build_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>HelloWorld</title>
  <file_id>4</file_id>
  <build/>
  <size>0</size>
</build_file>
""".strip()

build_file_put_xml = \
"""
<build_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>newtitle</title>
  <file_id>4</file_id>
  <size>0</size>
</build_file>
""".strip()