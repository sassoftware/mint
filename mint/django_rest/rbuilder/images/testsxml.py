images_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<images count="3" next_page="" num_pages="1" previous_page="" full_collection="" end_index="2" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <image id="http://testserver/api/v1/images/1">
    <actions/>
    <files>
      <file>
        <sha1>0</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/1"/>
        <file_id>1</file_id>
        <size>0</size>
      </file>
      <file>
        <sha1>1</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=2&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/1"/>
        <file_id>2</file_id>
        <size>1</size>
      </file>
    </files>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-0-1</trailing_version>
    <num_image_files>2</num_image_files>
    <image_type id="http://testserver/api/v1/image_types/10">
      <description>VHD for Microsoft(R) Hyper-V(R)</description>
      <image_type_id>10</image_type_id>
      <key>VIRTUAL_PC_IMAGE</key>
      <name>Microsoft (R) Hyper-V</name>
    </image_type>
    <build_log id="http://testserver/api/v1/images/1/build_log"/>
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
    <image_id>1</image_id>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-0</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
    <released>True</released>
    <project id="http://testserver/api/v1/projects/foo0">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo0</short_name>
      <name>foo0</name>
    </project>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <base_image/>
    <release id="http://testserver/api/v1/releases/1"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
    <jobs id="http://testserver/api/v1/images/1/jobs"/>
  </image>
  <image id="http://testserver/api/v1/images/2">
    <actions/>
    <files>
      <file>
        <sha1>1</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=3&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/2"/>
        <file_id>3</file_id>
        <size>1</size>
      </file>
      <file>
        <sha1>2</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=4&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/2"/>
        <file_id>4</file_id>
        <size>2</size>
      </file>
    </files>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-1-1</trailing_version>
    <num_image_files>2</num_image_files>
    <image_type id="http://testserver/api/v1/image_types/10">
      <description>VHD for Microsoft(R) Hyper-V(R)</description>
      <image_type_id>10</image_type_id>
      <key>VIRTUAL_PC_IMAGE</key>
      <name>Microsoft (R) Hyper-V</name>
    </image_type>
    <build_log id="http://testserver/api/v1/images/2/build_log"/>
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
    <image_id>2</image_id>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-1</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
    <released>True</released>
    <project id="http://testserver/api/v1/projects/foo1">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo1</short_name>
      <name>foo1</name>
    </project>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <base_image/>
    <release id="http://testserver/api/v1/releases/2"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
    <jobs id="http://testserver/api/v1/images/2/jobs"/>
  </image>
  <image id="http://testserver/api/v1/images/3">
    <actions/>
    <files>
      <file>
        <sha1>2</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=5&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/3"/>
        <file_id>5</file_id>
        <size>2</size>
      </file>
      <file>
        <sha1>3</sha1>
        <idx>0</idx>
        <title>foo</title>
        <url>http://testserver/downloadImage?fileId=6&amp;urlType=0</url>
        <image id="http://testserver/api/v1/images/3"/>
        <file_id>6</file_id>
        <size>3</size>
      </file>
    </files>
    <trove_last_changed></trove_last_changed>
    <updated_by id="http://testserver/api/v1/users/2002"/>
    <trailing_version>1-2-1</trailing_version>
    <num_image_files>2</num_image_files>
    <image_type id="http://testserver/api/v1/image_types/10">
      <description>VHD for Microsoft(R) Hyper-V(R)</description>
      <image_type_id>10</image_type_id>
      <key>VIRTUAL_PC_IMAGE</key>
      <name>Microsoft (R) Hyper-V</name>
    </image_type>
    <build_log id="http://testserver/api/v1/images/3/build_log"/>
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
    <image_id>3</image_id>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-2</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-2-1</trove_version>
    <released>True</released>
    <project id="http://testserver/api/v1/projects/foo2">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo2</short_name>
      <name>foo2</name>
    </project>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <base_image/>
    <release id="http://testserver/api/v1/releases/3"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
    <jobs id="http://testserver/api/v1/images/3/jobs"/>
  </image>
</images>
""".strip()

image_get_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<image id="http://testserver/api/v1/images/1">
  <actions>
    <action>
      <description>Cancel image build</description>
      <descriptor id="http://testserver/api/v1/images/1/descriptors/cancel_build"/>
      <enabled>True</enabled>
      <job_type id="http://testserver/api/v1/inventory/event_types/25"/>
      <key>image_build_cancellation</key>
      <name>Cancel image build</name>
    </action>
  </actions>
  <files>
    <file>
      <sha1>0</sha1>
      <idx>0</idx>
      <title>foo</title>
      <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
      <image id="http://testserver/api/v1/images/1"/>
      <file_id>1</file_id>
      <size>0</size>
    </file>
    <file>
      <sha1>1</sha1>
      <idx>0</idx>
      <title>foo</title>
      <url>http://testserver/downloadImage?fileId=2&amp;urlType=0</url>
      <image id="http://testserver/api/v1/images/1"/>
      <file_id>2</file_id>
      <size>1</size>
    </file>
  </files>
  <trove_last_changed></trove_last_changed>
  <updated_by id="http://testserver/api/v1/users/2002"/>
  <trailing_version>1-0-1</trailing_version>
  <num_image_files>2</num_image_files>
  <image_type id="http://testserver/api/v1/image_types/10">
    <description>VHD for Microsoft(R) Hyper-V(R)</description>
    <image_type_id>10</image_type_id>
    <key>VIRTUAL_PC_IMAGE</key>
    <name>Microsoft (R) Hyper-V</name>
  </image_type>
  <build_log id="http://testserver/api/v1/images/1/build_log"/>
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
  <image_id>1</image_id>
  <time_created></time_created>
  <time_updated></time_updated>
  <name>image-0</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
  <released>True</released>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <output_trove></output_trove>
  <architecture>x86</architecture>
  <base_image/>
  <release id="http://testserver/api/v1/releases/1"/>
  <image_count>1</image_count>
  <job_uuid>1</job_uuid>
  <jobs id="http://testserver/api/v1/images/1/jobs"/>
</image>
"""

build_file_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>foo</title>
  <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
  <image id="http://testserver/api/v1/images/1"/>
  <file_id>1</file_id>
  <size>0</size>
</file>
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
  <image_type id="http://testserver/api/v1/image_types/10">
    <description>VHD for Microsoft(R) Hyper-V(R)</description>
    <image_type_id>10</image_type_id>
    <key>VIRTUAL_PC_IMAGE</key>
    <name>Microsoft (R) Hyper-V</name>
  </image_type>
  <time_updated></time_updated>
  <name>image-20</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
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
  <image_type id="http://testserver/api/v1/image_types/10">
    <description>VHD for Microsoft(R) Hyper-V(R)</description>
    <image_type_id>10</image_type_id>
    <key>VIRTUAL_PC_IMAGE</key>
    <name>Microsoft (R) Hyper-V</name>
  </image_type>
  <time_updated></time_updated>
  <name>image-20</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
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
<file>
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
      <image_type id="http://testserver/api/v1/image_types/10">
        <description>VHD for Microsoft(R) Hyper-V(R)</description>
        <image_type_id>10</image_type_id>
        <key>VIRTUAL_PC_IMAGE</key>
        <name>Microsoft (R) Hyper-V</name>
      </image_type>
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
</file>
""".strip()

build_files_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<files count="2" next_page="" num_pages="1" previous_page="" full_collection="" end_index="1" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <file>
    <sha1>0</sha1>
    <idx>0</idx>
    <title>foo</title>
    <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
    <image id="http://testserver/api/v1/images/1"/>
    <file_id>1</file_id>
    <size>0</size>
  </file>
  <file>
    <sha1>1</sha1>
    <idx>0</idx>
    <title>foo</title>
    <url>http://testserver/downloadImage?fileId=2&amp;urlType=0</url>
    <image id="http://testserver/api/v1/images/1"/>
    <file_id>2</file_id>
    <size>1</size>
  </file>
</files>

""".strip()

build_file_posted_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>HelloWorld</title>
  <image id="http://testserver/api/v1/images/4"/>
  <file_id>7</file_id>
  <size>0</size>
</file>

""".strip()

build_file_put_xml = \
"""
<file>
  <sha1>0</sha1>
  <idx>0</idx>
  <title>newtitle</title>
  <file_id>4</file_id>
  <size>0</size>
</file>
""".strip()

release_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<release id="http://testserver/api/v1/releases/1">
  <release_id>1</release_id>
  <description>description0</description>
  <num_images>1</num_images>
  <time_created></time_created>
  <name>release0</name>
  <project id="http://testserver/api/v1/projects/foo0">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>foo0</short_name>
    <name>foo0</name>
  </project>
  <should_mirror>0</should_mirror>
  <published_by id="http://testserver/api/v1/users/2005">
    <user_name>janephoo</user_name>
    <full_name>Jane Phoo</full_name>
  </published_by>
  <time_updated></time_updated>
  <created_by id="http://testserver/api/v1/users/2004">
    <user_name>jimphoo</user_name>
    <full_name>Jim Phoo</full_name>
  </created_by>
  <version>releaseVersion0</version>
  <published>True</published>
  <images id="http://testserver/api/v1/releases/1/images">
    <image id="http://testserver/api/v1/images/1">
      <files>
        <file>
          <sha1>0</sha1>
          <idx>0</idx>
          <title>foo</title>
          <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
          <image id="http://testserver/api/v1/images/1"/>
          <file_id>1</file_id>
          <size>0</size>
        </file>
        <file>
          <sha1>1</sha1>
          <idx>0</idx>
          <title>foo</title>
          <url>http://testserver/downloadImage?fileId=2&amp;urlType=0</url>
          <image id="http://testserver/api/v1/images/1"/>
          <file_id>2</file_id>
          <size>1</size>
        </file>
      </files>
      <actions>
        <action>
          <description>Cancel image build</description>
          <descriptor id="http://testserver/api/v1/images/1/descriptors/cancel_build"/>
          <enabled>True</enabled>
          <job_type id="http://testserver/api/v1/inventory/event_types/25"/>
          <key>image_build_cancellation</key>
          <name>Cancel image build</name>
        </action>
      </actions>
      <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
        <name>trunk</name>
      </project_branch>
      <updated_by id="http://testserver/api/v1/users/2005">
        <user_name>janephoo</user_name>
        <full_name>Jane Phoo</full_name>
      </updated_by>
      <trailing_version>1-0-1</trailing_version>
      <num_image_files>2</num_image_files>
      <image_type id="http://testserver/api/v1/image_types/10">
        <description>VHD for Microsoft(R) Hyper-V(R)</description>
        <name>Microsoft (R) Hyper-V</name>
        <key>VIRTUAL_PC_IMAGE</key>
        <image_type_id>10</image_type_id>
      </image_type>
      <build_log id="http://testserver/api/v1/images/1/build_log"/>
      <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
      <created_by id="http://testserver/api/v1/users/2004">
        <user_name>jimphoo</user_name>
        <full_name>Jim Phoo</full_name>
      </created_by>
      <base_image></base_image>
      <status_message></status_message>
      <trove_name>troveName0</trove_name>
      <status>-1</status>
      <stage_name>stage0</stage_name>
      <jobs id="http://testserver/api/v1/images/1/jobs"/>
      <description>image-0</description>
      <image_id>1</image_id>
      <trove_last_changed></trove_last_changed>
      <time_updated></time_updated>
      <name>image-0</name>
      <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
      <released>True</released>
      <project id="http://testserver/api/v1/projects/foo0">
        <domain_name>eng.rpath.com</domain_name>
        <short_name>foo0</short_name>
        <name>foo0</name>
      </project>
      <output_trove></output_trove>
      <architecture>x86</architecture>
      <time_created></time_created>
      <release id="http://testserver/api/v1/releases/1"/>
      <image_count>1</image_count>
      <job_uuid>1</job_uuid>
    </image>
  </images>
  <time_mirrored></time_mirrored>
  <time_published></time_published>
  <updated_by id="http://testserver/api/v1/users/2005">
    <user_name>janephoo</user_name>
    <full_name>Jane Phoo</full_name>
  </updated_by>
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
  <published>True</published>
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
    <description>description0</description>
    <num_images>1</num_images>
    <time_created></time_created>
    <name>release0</name>
    <project id="http://testserver/api/v1/projects/foo0">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo0</short_name>
      <name>foo0</name>
    </project>
    <should_mirror>0</should_mirror>
    <published_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </published_by>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2004">
      <user_name>jimphoo</user_name>
      <full_name>Jim Phoo</full_name>
    </created_by>
    <version>releaseVersion0</version>
    <published>True</published>
    <images id="http://testserver/api/v1/releases/1/images">
      <image id="http://testserver/api/v1/images/1">
        <files>
          <file>
            <sha1>0</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=1&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/1"/>
            <file_id>1</file_id>
            <size>0</size>
          </file>
          <file>
            <sha1>1</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=2&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/1"/>
            <file_id>2</file_id>
            <size>1</size>
          </file>
        </files>
        <actions>
          <action>
            <description>Cancel image build</description>
            <descriptor id="http://testserver/api/v1/images/1/descriptors/cancel_build"/>
            <enabled>True</enabled>
            <job_type id="http://testserver/api/v1/inventory/event_types/25"/>
            <key>image_build_cancellation</key>
            <name>Cancel image build</name>
          </action>
        </actions>
        <project_branch id="http://testserver/api/v1/projects/foo0/project_branches/foo0.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <updated_by id="http://testserver/api/v1/users/2005">
          <user_name>janephoo</user_name>
          <full_name>Jane Phoo</full_name>
        </updated_by>
        <trailing_version>1-0-1</trailing_version>
        <num_image_files>2</num_image_files>
        <image_type id="http://testserver/api/v1/image_types/10">
          <description>VHD for Microsoft(R) Hyper-V(R)</description>
          <name>Microsoft (R) Hyper-V</name>
          <key>VIRTUAL_PC_IMAGE</key>
          <image_type_id>10</image_type_id>
        </image_type>
        <build_log id="http://testserver/api/v1/images/1/build_log"/>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <created_by id="http://testserver/api/v1/users/2004">
          <user_name>jimphoo</user_name>
          <full_name>Jim Phoo</full_name>
        </created_by>
        <base_image></base_image>
        <status_message></status_message>
        <trove_name>troveName0</trove_name>
        <status>-1</status>
        <stage_name>stage0</stage_name>
        <jobs id="http://testserver/api/v1/images/1/jobs"/>
        <description>image-0</description>
        <image_id>1</image_id>
        <trove_last_changed></trove_last_changed>
        <time_updated></time_updated>
        <name>image-0</name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-0-1</trove_version>
        <released>True</released>
        <project id="http://testserver/api/v1/projects/foo0">
          <domain_name>eng.rpath.com</domain_name>
          <short_name>foo0</short_name>
          <name>foo0</name>
        </project>
        <output_trove></output_trove>
        <architecture>x86</architecture>
        <time_created></time_created>
        <release id="http://testserver/api/v1/releases/1"/>
        <image_count>1</image_count>
        <job_uuid>1</job_uuid>
      </image>
    </images>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </updated_by>
  </release>
  <release id="http://testserver/api/v1/releases/2">
    <release_id>2</release_id>
    <description>description1</description>
    <num_images>1</num_images>
    <time_created></time_created>
    <name>release1</name>
    <project id="http://testserver/api/v1/projects/foo1">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo1</short_name>
      <name>foo1</name>
    </project>
    <should_mirror>0</should_mirror>
    <published_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </published_by>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2004">
      <user_name>jimphoo</user_name>
      <full_name>Jim Phoo</full_name>
    </created_by>
    <version>releaseVersion1</version>
    <published>True</published>
    <images id="http://testserver/api/v1/releases/2/images">
      <image id="http://testserver/api/v1/images/2">
        <files>
          <file>
            <sha1>1</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=3&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/2"/>
            <file_id>3</file_id>
            <size>1</size>
          </file>
          <file>
            <sha1>2</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=4&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/2"/>
            <file_id>4</file_id>
            <size>2</size>
          </file>
        </files>
        <actions>
          <action>
            <description>Cancel image build</description>
            <descriptor id="http://testserver/api/v1/images/2/descriptors/cancel_build"/>
            <enabled>True</enabled>
            <job_type id="http://testserver/api/v1/inventory/event_types/25"/>
            <key>image_build_cancellation</key>
            <name>Cancel image build</name>
          </action>
        </actions>
        <project_branch id="http://testserver/api/v1/projects/foo1/project_branches/foo1.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <updated_by id="http://testserver/api/v1/users/2005">
          <user_name>janephoo</user_name>
          <full_name>Jane Phoo</full_name>
        </updated_by>
        <trailing_version>1-1-1</trailing_version>
        <num_image_files>2</num_image_files>
        <image_type id="http://testserver/api/v1/image_types/10">
          <description>VHD for Microsoft(R) Hyper-V(R)</description>
          <name>Microsoft (R) Hyper-V</name>
          <key>VIRTUAL_PC_IMAGE</key>
          <image_type_id>10</image_type_id>
        </image_type>
        <build_log id="http://testserver/api/v1/images/2/build_log"/>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <created_by id="http://testserver/api/v1/users/2004">
          <user_name>jimphoo</user_name>
          <full_name>Jim Phoo</full_name>
        </created_by>
        <base_image></base_image>
        <status_message></status_message>
        <trove_name>troveName1</trove_name>
        <status>-1</status>
        <stage_name>stage1</stage_name>
        <jobs id="http://testserver/api/v1/images/2/jobs"/>
        <description>image-1</description>
        <image_id>2</image_id>
        <trove_last_changed></trove_last_changed>
        <time_updated></time_updated>
        <name>image-1</name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
        <released>True</released>
        <project id="http://testserver/api/v1/projects/foo1">
          <domain_name>eng.rpath.com</domain_name>
          <short_name>foo1</short_name>
          <name>foo1</name>
        </project>
        <output_trove></output_trove>
        <architecture>x86</architecture>
        <time_created></time_created>
        <release id="http://testserver/api/v1/releases/2"/>
        <image_count>1</image_count>
        <job_uuid>1</job_uuid>
      </image>
    </images>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </updated_by>
  </release>
  <release id="http://testserver/api/v1/releases/3">
    <release_id>3</release_id>
    <description>description2</description>
    <num_images>1</num_images>
    <time_created></time_created>
    <name>release2</name>
    <project id="http://testserver/api/v1/projects/foo2">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>foo2</short_name>
      <name>foo2</name>
    </project>
    <should_mirror>0</should_mirror>
    <published_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </published_by>
    <time_updated></time_updated>
    <created_by id="http://testserver/api/v1/users/2004">
      <user_name>jimphoo</user_name>
      <full_name>Jim Phoo</full_name>
    </created_by>
    <version>releaseVersion2</version>
    <published>True</published>
    <images id="http://testserver/api/v1/releases/3/images">
      <image id="http://testserver/api/v1/images/3">
        <files>
          <file>
            <sha1>2</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=5&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/3"/>
            <file_id>5</file_id>
            <size>2</size>
          </file>
          <file>
            <sha1>3</sha1>
            <idx>0</idx>
            <title>foo</title>
            <url>http://testserver/downloadImage?fileId=6&amp;urlType=0</url>
            <image id="http://testserver/api/v1/images/3"/>
            <file_id>6</file_id>
            <size>3</size>
          </file>
        </files>
        <actions/>
        <project_branch id="http://testserver/api/v1/projects/foo2/project_branches/foo2.eng.rpath.com@rpath:foo-trunk">
          <name>trunk</name>
        </project_branch>
        <updated_by id="http://testserver/api/v1/users/2005">
          <user_name>janephoo</user_name>
          <full_name>Jane Phoo</full_name>
        </updated_by>
        <trailing_version>1-2-1</trailing_version>
        <num_image_files>2</num_image_files>
        <image_type id="http://testserver/api/v1/image_types/10">
          <description>VHD for Microsoft(R) Hyper-V(R)</description>
          <name>Microsoft (R) Hyper-V</name>
          <key>VIRTUAL_PC_IMAGE</key>
          <image_type_id>10</image_type_id>
        </image_type>
        <build_log id="http://testserver/api/v1/images/3/build_log"/>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <created_by id="http://testserver/api/v1/users/2004">
          <user_name>jimphoo</user_name>
          <full_name>Jim Phoo</full_name>
        </created_by>
        <base_image></base_image>
        <status_message></status_message>
        <trove_name>troveName2</trove_name>
        <status>-1</status>
        <stage_name>stage2</stage_name>
        <jobs id="http://testserver/api/v1/images/3/jobs"/>
        <description>image-2</description>
        <image_id>3</image_id>
        <trove_last_changed></trove_last_changed>
        <time_updated></time_updated>
        <name>image-2</name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-2-1</trove_version>
        <released>True</released>
        <project id="http://testserver/api/v1/projects/foo2">
          <domain_name>eng.rpath.com</domain_name>
          <short_name>foo2</short_name>
          <name>foo2</name>
        </project>
        <output_trove></output_trove>
        <architecture>x86</architecture>
        <time_created></time_created>
        <release id="http://testserver/api/v1/releases/3"/>
        <image_count>1</image_count>
        <job_uuid>1</job_uuid>
      </image>
    </images>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by id="http://testserver/api/v1/users/2005">
      <user_name>janephoo</user_name>
      <full_name>Jane Phoo</full_name>
    </updated_by>
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

build_file_url_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<file_url>
  <url>http://example.com/0/</url>
  <url_type>0</url_type>
  <file_url_id>1</file_url_id>
</file_url>
""".strip()

image_types_get_xml = \
"""
<image_types count="22" next_page="http://testserver/api/v1/image_types;start_index=10;limit=10" num_pages="3" previous_page="" full_collection="http://testserver/api/v1/image_types" end_index="9" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/image_types;start_index=0;limit=10" start_index="0">
  <image_type id="http://testserver/api/v1/image_types/0">
    <description></description>
    <name></name>
    <key>BOOTABLE_IMAGE</key>
    <image_type_id>0</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/1">
    <description>Legacy Installable CD/DVD</description>
    <name>Inst CD/DVD</name>
    <key>INSTALLABLE_ISO</key>
    <image_type_id>1</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/2">
    <description>Stub Image</description>
    <name>Stub</name>
    <key>STUB_IMAGE</key>
    <image_type_id>2</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/3">
    <description>Eucalyptus/Mountable Filesystem</description>
    <name>Raw FS</name>
    <key>RAW_FS_IMAGE</key>
    <image_type_id>3</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/4">
    <description>Netboot Image</description>
    <name>Netboot</name>
    <key>NETBOOT_IMAGE</key>
    <image_type_id>4</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/5">
    <description>TAR File</description>
    <name>Tar</name>
    <key>TARBALL</key>
    <image_type_id>5</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/6">
    <description>Demo CD/DVD (Live CD/DVD)</description>
    <name>Demo CD/DVD</name>
    <key>LIVE_ISO</key>
    <image_type_id>6</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/7">
    <description>KVM/Parallels/QEMU/Raw Hard Disk</description>
    <name>HDD</name>
    <key>RAW_HD_IMAGE</key>
    <image_type_id>7</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/8">
    <description>VMware(R) Workstation/Fusion Virtual Appliance</description>
    <name>VMware (R)</name>
    <key>VMWARE_IMAGE</key>
    <image_type_id>8</image_type_id>
  </image_type>
  <image_type id="http://testserver/api/v1/image_types/9">
    <description>VMware(R) ESX/VCD Virtual Appliance</description>
    <name>VMware (R) ESX</name>
    <key>VMWARE_ESX_IMAGE</key>
    <image_type_id>9</image_type_id>
  </image_type>
</image_types>
"""

image_type_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image_type id="http://testserver/api/v1/image_types/1">
  <description>Legacy Installable CD/DVD</description>
  <name>Inst CD/DVD</name>
  <key>INSTALLABLE_ISO</key>
  <image_type_id>1</image_type_id>
</image_type>
"""
