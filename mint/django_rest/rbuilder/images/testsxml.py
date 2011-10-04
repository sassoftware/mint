images_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<images count="3" next_page="" num_pages="1" previous_page="" full_collection="" end_index="2" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <image id="http://testserver/api/v1/images/1">
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-0-1</trailing_version>
    <image_type>10</image_type>
    <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <status_message></status_message>
    <trove_name>troveName0</trove_name>
    <status>-1</status>
    <stage_name>stage0</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-0</description>
    <released>True</released>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-0</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
    <image_id>1</image_id>
    <image_files>
      <image_file>
        <sha1>0</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/1"/>
        <file_id>1</file_id>
        <size>0</size>
      </image_file>
      <image_file>
        <sha1>1</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/1"/>
        <file_id>2</file_id>
        <size>1</size>
      </image_file>
    </image_files>
    <project id="http://testserver/api/v1/projects/foo0">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo0</short_name>
      <name>foo0</name>
    </project>
    <num_image_files>2</num_image_files>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <release id="http://testserver/api/v1/releases/1"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
  </image>
  <image id="http://testserver/api/v1/images/2">
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-1-1</trailing_version>
    <image_type>10</image_type>
    <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <status_message></status_message>
    <trove_name>troveName1</trove_name>
    <status>-1</status>
    <stage_name>stage1</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo1/project_branches/foo1.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-1</description>
    <released>True</released>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-1</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
    <image_id>2</image_id>
    <image_files>
      <image_file>
        <sha1>1</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/2"/>
        <file_id>3</file_id>
        <size>1</size>
      </image_file>
      <image_file>
        <sha1>2</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/2"/>
        <file_id>4</file_id>
        <size>2</size>
      </image_file>
    </image_files>
    <project id="http://testserver/api/v1/projects/foo1">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo1</short_name>
      <name>foo1</name>
    </project>
    <num_image_files>2</num_image_files>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <release id="http://testserver/api/v1/releases/2"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
  </image>
  <image id="http://testserver/api/v1/images/3">
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-2-1</trailing_version>
    <image_type>10</image_type>
    <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <status_message></status_message>
    <trove_name>troveName2</trove_name>
    <status>-1</status>
    <stage_name>stage2</stage_name>
    <project_branch id="http://testserver/api/v1/projects/foo2/project_branches/foo2.eng.rpath.com@rpath:foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-2</description>
    <released>True</released>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-2</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-2-1</trove_version>
    <image_id>3</image_id>
    <image_files>
      <image_file>
        <sha1>2</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/3"/>
        <file_id>5</file_id>
        <size>2</size>
      </image_file>
      <image_file>
        <sha1>3</sha1>
        <idx>0</idx>
        <title></title>
        <image id="http://testserver/api/v1/images/3"/>
        <file_id>6</file_id>
        <size>3</size>
      </image_file>
    </image_files>
    <project id="http://testserver/api/v1/projects/foo2">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo2</short_name>
      <name>foo2</name>
    </project>
    <num_image_files>2</num_image_files>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <release id="http://testserver/api/v1/releases/3"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
  </image>
</images>
"""

image_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<image id="http://testserver/api/v1/images/1">
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trailing_version>1-0-1</trailing_version>
  <image_type>10</image_type>
  <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <status_message></status_message>
  <trove_name>troveName0</trove_name>
  <status>-1</status>
  <stage_name>stage0</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-0</description>
  <released>True</released>
  <time_created></time_created>
  <time_updated></time_updated>
  <name>image-0</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
  <image_id>1</image_id>
  <image_files>
    <image_file>
      <sha1>0</sha1>
      <idx>0</idx>
      <title></title>
      <image id="http://testserver/api/v1/images/1"/>
      <file_id>1</file_id>
      <size>0</size>
    </image_file>
    <image_file>
      <sha1>1</sha1>
      <idx>0</idx>
      <title></title>
      <image id="http://testserver/api/v1/images/1"/>
      <file_id>2</file_id>
      <size>1</size>
    </image_file>
  </image_files>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <num_image_files>2</num_image_files>
  <output_trove></output_trove>
  <architecture>x86</architecture>
  <release id="http://testserver/api/v1/releases/1"/>
  <image_count>1</image_count>
  <job_uuid>1</job_uuid>
</image>
"""

build_file_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title></title>
  <file_id>1</file_id>
  <image id="http://testserver/api/v1/images/1"/>
  <size>0</size>
</image_file>
""".strip()

image_post_xml = """
<image>
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trove_flavor>is: x86</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <status_message></status_message>
  <trove_name>troveName20</trove_name>
  <image_count>1</image_count>
  <status>-1</status>
  <stage_name>stage20</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-20</description>
  <time_created></time_created>
  <image_type>10</image_type>
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
  <status_message></status_message>
  <trove_name>troveName20-Changed</trove_name>
  <image_count>1</image_count>
  <status>-1</status>
  <stage_name>stage20</stage_name>
  <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-20</description>
  <time_created></time_created>
  <image_type>10</image_type>
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
<image_file>
    <image>
      <trove_last_changed></trove_last_changed>
      <updated_by id="http://testserver/api/v1/users/2002"/>
      <trove_flavor>is: x86</trove_flavor>
      <created_by id="http://testserver/api/v1/users/2001"/>
      <status_message></status_message>
      <trove_name>troveName20-Changed</trove_name>
      <image_count>1</image_count>
      <status>-1</status>
      <stage_name>stage20</stage_name>
      <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
        <name>trunk</name>
      </project_branch>
      <description>image-20</description>
      <time_created></time_created>
      <image_type>10</image_type>
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
    <sha1>0</sha1>
    <idx>0</idx>
    <title>HelloWorld</title>
    <size>0</size>
</image_file>
""".strip()

build_files_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image_files count="2" next_page="" num_pages="1" previous_page="" full_collection="" end_index="1" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <image_file>
    <sha1>0</sha1>
    <idx>0</idx>
    <title></title>
    <image id="http://testserver/api/v1/images/1"/>
    <file_id>1</file_id>
    <size>0</size>
  </image_file>
  <image_file>
    <sha1>1</sha1>
    <idx>0</idx>
    <title></title>
    <image id="http://testserver/api/v1/images/1"/>
    <file_id>2</file_id>
    <size>1</size>
  </image_file>
</image_files>
""".strip()

build_file_posted_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>HelloWorld</title>
  <image id="http://testserver/api/v1/images/4"/>
  <file_id>7</file_id>
  <size>0</size>
</image_file>

""".strip()

build_file_put_xml = \
"""
<image_file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>newtitle</title>
  <file_id>4</file_id>
  <size>0</size>
</image_file>
""".strip()

release_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<release id="http://testserver/api/v1/releases/1">
  <release_id>1</release_id>
  <name>release0</name>
  <description>description0</description>
  <images>
    <image id="http://testserver/api/v1/images/1">
      <architecture>x86</architecture>
      <created_by id="http://testserver/api/v1/users/2001"/>
      <description>image-0</description>
      <image_count>1</image_count>
      <image_files>
        <image_file>
          <file_id>1</file_id>
          <idx>0</idx>
          <image id="http://testserver/api/v1/images/1"/>
          <sha1>0</sha1>
          <size>0</size>
          <title/>
        </image_file>
        <image_file>
          <file_id>2</file_id>
          <idx>0</idx>
          <image id="http://testserver/api/v1/images/1"/>
          <sha1>1</sha1>
          <size>1</size>
          <title/>
        </image_file>
      </image_files>
      <image_id>1</image_id>
      <image_type>10</image_type>
      <job_uuid>1</job_uuid>
      <name>image-0</name>
      <num_image_files>2</num_image_files>
      <output_trove/>
      <project id="http://testserver/api/v1/projects/foo0">
        <domain_name>eng.rpath.com</domain_name>
        <name>foo0</name>
        <short_name>foo0</short_name>
      </project>
      <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
        <name>trunk</name>
      </project_branch>
      <release id="http://testserver/api/v1/releases/1"/>
      <released>True</released>
      <stage_name>stage0</stage_name>
      <status>-1</status>
      <status_message/>
      <trailing_version>1-0-1</trailing_version>
      <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
      <trove_last_changed/>
      <trove_name>troveName0</trove_name>
      <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
      <updated_by id="http://testserver/api/v1/users/2002"/>
    </image>
  </images>
  <time_created></time_created>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <published_by id="http://testserver/api/v1/users/2002"/>
  <time_updated></time_updated>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <version>releaseVersion0</version>
  <should_mirror>0</should_mirror>
  <time_mirrored></time_mirrored>
  <time_published></time_published>
  <updated_by id="http://testserver/api/v1/users/2002"/>
</release>
""".strip()


release_post_xml = \
"""
<release>
  <name>release100</name>
  <description>description100</description>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <published_by id="http://testserver/api/v1/users/2002"/>
  <time_updated></time_updated>
  <created_by id="http://testserver/api/v1/users/2001"/>
  <version>releaseVersion100</version>
  <should_mirror>0</should_mirror>
  <updated_by id="http://testserver/api/v1/users/2002"/>
</release>
""".strip()

releases_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<releases count="3" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/releases" end_index="2" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/releases;start_index=0;limit=10" start_index="0">
  <release id="http://testserver/api/v1/releases/1">
    <release_id>1</release_id>
    <name>release0</name>
    <description>description0</description>
    <images>
      <image id="http://testserver/api/v1/images/1">
        <architecture>x86</architecture>
        <created_by id="http://testserver/api/v1/users/2001"/>
        <description>image-0</description>
        <image_count>1</image_count>
        <image_files>
          <image_file>
            <file_id>1</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/1"/>
            <sha1>0</sha1>
            <size>0</size>
            <title/>
          </image_file>
          <image_file>
            <file_id>2</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/1"/>
            <sha1>1</sha1>
            <size>1</size>
            <title/>
          </image_file>
        </image_files>
        <image_id>1</image_id>
        <image_type>10</image_type>
        <job_uuid>1</job_uuid>
        <name>image-0</name>
        <num_image_files>2</num_image_files>
        <output_trove/>
        <project id="http://testserver/api/v1/projects/foo0">
          <domain_name>eng.rpath.com</domain_name>
          <name>foo0</name>
          <short_name>foo0</short_name>
        </project>
        <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <release id="http://testserver/api/v1/releases/1"/>
        <released>True</released>
        <stage_name>stage0</stage_name>
        <status>-1</status>
        <status_message/>
        <trailing_version>1-0-1</trailing_version>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <trove_last_changed/>
        <trove_name>troveName0</trove_name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
        <updated_by id="http://testserver/api/v1/users/2002"/>
      </image>
    </images>
    <time_created></time_created>
    <project id="http://testserver/api/v1/projects/foo0">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo0</short_name>
      <name>foo0</name>
    </project>
    <published_by id="http://testserver/api/v1/users/2002"/>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <version>releaseVersion0</version>
    <should_mirror>0</should_mirror>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2002"/>
  </release>
  <release id="http://testserver/api/v1/releases/2">
    <release_id>2</release_id>
    <images>
      <image id="http://testserver/api/v1/images/2">
        <architecture>x86</architecture>
        <created_by id="http://testserver/api/v1/users/2001"/>
        <description>image-1</description>
        <image_count>1</image_count>
        <image_files>
          <image_file>
            <file_id>3</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/2"/>
            <sha1>1</sha1>
            <size>1</size>
            <title/>
          </image_file>
          <image_file>
            <file_id>4</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/2"/>
            <sha1>2</sha1>
            <size>2</size>
            <title/>
          </image_file>
        </image_files>
        <image_id>2</image_id>
        <image_type>10</image_type>
        <job_uuid>1</job_uuid>
        <name>image-1</name>
        <num_image_files>2</num_image_files>
        <output_trove/>
        <project id="http://testserver/api/v1/projects/foo1">
          <domain_name>eng.rpath.com</domain_name>
          <name>foo1</name>
          <short_name>foo1</short_name>
        </project>
        <project_branch id="http://testserver/api/v1/projects/foo1/project_branches/foo1.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <release id="http://testserver/api/v1/releases/2"/>
        <released>True</released>
        <stage_name>stage1</stage_name>
        <status>-1</status>
        <status_message/>
        <trailing_version>1-1-1</trailing_version>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <trove_last_changed/>
        <trove_name>troveName1</trove_name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
        <updated_by id="http://testserver/api/v1/users/2002"/>
      </image>
    </images>
    <name>release1</name>
    <description>description1</description>
    <time_created></time_created>
    <project id="http://testserver/api/v1/projects/foo1">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo1</short_name>
      <name>foo1</name>
    </project>
    <published_by id="http://testserver/api/v1/users/2002"/>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <version>releaseVersion1</version>
    <should_mirror>0</should_mirror>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2002"/>
  </release>
  <release id="http://testserver/api/v1/releases/3">
    <release_id>3</release_id>
    <images>
      <image id="http://testserver/api/v1/images/3">
        <architecture>x86</architecture>
        <created_by id="http://testserver/api/v1/users/2001"/>
        <description>image-2</description>
        <image_count>1</image_count>
        <image_files>
          <image_file>
            <file_id>5</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/3"/>
            <sha1>2</sha1>
            <size>2</size>
            <title/>
          </image_file>
          <image_file>
            <file_id>6</file_id>
            <idx>0</idx>
            <image id="http://testserver/api/v1/images/3"/>
            <sha1>3</sha1>
            <size>3</size>
            <title/>
          </image_file>
        </image_files>
        <image_id>3</image_id>
        <image_type>10</image_type>
        <job_uuid>1</job_uuid>
        <name>image-2</name>
        <num_image_files>2</num_image_files>
        <output_trove/>
        <project id="http://testserver/api/v1/projects/foo2">
          <domain_name>eng.rpath.com</domain_name>
          <name>foo2</name>
          <short_name>foo2</short_name>
        </project>
        <project_branch id="http://testserver/api/v1/projects/foo2/project_branches/foo2.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <release id="http://testserver/api/v1/releases/3"/>
        <released>True</released>
        <stage_name>stage2</stage_name>
        <status>-1</status>
        <status_message/>
        <trailing_version>1-2-1</trailing_version>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <trove_last_changed/>
        <trove_name>troveName2</trove_name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-2-1</trove_version>
        <updated_by id="http://testserver/api/v1/users/2002"/>
      </image>
    </images>
    <name>release2</name>
    <description>description2</description>
    <time_created></time_created>
    <project id="http://testserver/api/v1/projects/foo2">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo2</short_name>
      <name>foo2</name>
    </project>
    <published_by id="http://testserver/api/v1/users/2002"/>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2001"/>
    <version>releaseVersion2</version>
    <should_mirror>0</should_mirror>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2002"/>
  </release>
</releases>
""".strip()

release_put_xml = \
"""
<release id="http://testserver/api/v1/releases/1">
  <release_id>1</release_id>
  <name>release100</name>
  <description>description100</description>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <version>releaseVersion100</version>
  <should_mirror>0</should_mirror>
</release>
""".strip()

downloads_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<url_downloads count="2" next_page="" num_pages="1" previous_page="" full_collection="" end_index="1" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <url_download>
    <url/>
    <time_downloaded>0.0</time_downloaded>
    <ip>127.0.0.1</ip>
    <url_download_id>5</url_download_id>
  </url_download>
  <url_download>
    <url/>
    <time_downloaded>0.0</time_downloaded>
    <ip>192.160.1.1</ip>
    <url_download_id>6</url_download_id>
  </url_download>
</url_downloads>
""".strip()

download_post_xml = \
"""
<url_download>
  <url>
    <url>http://example.com/20/</url>
    <url_type>0</url_type>
  </url>
  <time_downloaded>0.0</time_downloaded>
  <ip>127.0.0.6</ip>
</url_download>
"""

build_file_url_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<file_url>
  <url>http://example.com/0/</url>
  <url_downloads>
    <url_download>
      <url/>
      <time_downloaded>0.0</time_downloaded>
      <ip>127.0.0.0</ip>
      <url_download_id>1</url_download_id>
    </url_download>
    <url_download>
      <url/>
      <time_downloaded>0.0</time_downloaded>
      <ip>192.160.1.0</ip>
      <url_download_id>2</url_download_id>
    </url_download>
  </url_downloads>
  <url_type>0</url_type>
  <file_url_id>1</file_url_id>
</file_url>
""".strip()