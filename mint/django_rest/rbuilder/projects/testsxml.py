#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

projects_xml = """\
"""

project_post_xml = """\
  <project>
    <commit_email>test@example.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>test-project</short_name>
    <hostname>test-project</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <repository_hostname>test-project.eng.rpath.com</repository_hostname>
    <external>false</external>
    <name>test-project</name>
  </project>
"""

project_post_no_hostname_xml = """\
  <project>
    <commit_email>test@example.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>test-project</short_name>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <repository_hostname>test-project.eng.rpath.com</repository_hostname>
    <external>false</external>
    <name>test-project</name>
  </project>
"""

project_post_no_namespace_xml = """\
  <project>
    <commit_email>test@example.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>test-project</short_name>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <repository_hostname>test-project.eng.rpath.com</repository_hostname>
    <external>false</external>
    <name>test-project</name>
  </project>
"""

project_post_no_repo_hostname_xml = """\
  <project>
    <commit_email>test@example.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>test-project</short_name>
    <hostname>test-project</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <external>false</external>
    <name>test-project</name>
  </project>
"""

project_post_no_domain_name_xml = """\
  <project>
    <commit_email>test@example.com</commit_email>
    <project_url>http://</project_url>
    <disabled>0</disabled>
    <isAppliance>1</isAppliance>
    <short_name>test-project</short_name>
    <hostname>test-project</hostname>
    <namespace>rpath</namespace>
    <hidden>false</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <external>false</external>
    <name>test-project</name>
  </project>
"""

project_post_external_xml = """\
  <project>
    <project_url>http://</project_url>
    <short_name>rwbs</short_name>
    <hostname>rwbs</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <external>true</external>
    <name>rPath Windows Build Service</name>
    <auth_type>userpass</auth_type>
    <entitlement/>
    <upstream_url>https://rb.rpath.com/repos/rwbs/browse</upstream_url>
    <label>rwbs.rb.rpath.com@rpath:rwbs-1-devel</label>
    <password>somepassword</password>
    <user_name>someuser</user_name>
  </project>
"""

project_post_external_no_url_no_auth_xml = """\
  <project>
    <project_url>http://</project_url>
    <short_name>rwbs</short_name>
    <hostname>rwbs</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <external>true</external>
    <name>rPath Windows Build Service</name>
    <auth_type>none</auth_type>
    <entitlement/>
    <label>rwbs.rb.rpath.com@rpath:rwbs-1-devel</label>
    <password>somepassword</password>
    <user_name>someuser</user_name>
  </project>
"""

project_post_external_no_url_external_auth_xml = """\
  <project>
    <project_url>http://</project_url>
    <short_name>rwbs</short_name>
    <hostname>rwbs</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>false</hidden>
    <description>test project description</description>
    <external>true</external>
    <name>rPath Windows Build Service</name>
    <auth_type>userpass</auth_type>
    <entitlement/>
    <label>rwbs.rb.rpath.com@rpath:rwbs-1-devel</label>
    <password>somepassword</password>
    <user_name>someuser</user_name>
  </project>
"""

project_put_xml = """\
  <project>
    <short_name>chater-foo</short_name>
    <description>updated description</description>
  </project>
"""

project_version_post_with_project_xml = """\
  <project_branch>
    <project id="http://testserver/api/v1/projects/foo"/>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
    <platform id="http://testserver/api/v1/platforms/1"/>
  </project_branch>
"""

project_version_post_with_project_xml2 = """\
  <project_branch>
    <project id="http://testserver/api/v1/projects/test-project"/>
    <description>2</description>
    <namespace>rpath</namespace>
    <name>50</name>
    <platform id="http://testserver/api/v1/platforms/1"/>
  </project_branch>
"""

project_version_post_with_project_no_auth_xml = """\
  <project_branch>
    <project id="http://127.0.0.1:8000/api/v1/projects/test-project"/>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
  </project_branch>
"""

project_version_put_xml = """\
  <project_branch id="http://testserver/api/v1/projects/postgres/project_branches/postgres.rpath.com@rpath:postgres-1">
    <description>updated description</description>
  </project_branch>
"""

project_branch_stage_xml = """\
<project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage">
  <groups href="http://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-stage"/>
  <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage/images"/>
  <label>foo@ns:trunk-stage</label>
  <name>Stage</name>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <name>chater-foo</name>
    <short_name>chater-foo</short_name>
  </project>
  <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
    <name>trunk</name>
  </project_branch>
  <promotable>false</promotable>
  <stage_id>12</stage_id>
</project_branch_stage>"""

project_branch_stage_put_xml = \
"""
<stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage">
  <groups href="http://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-stage"/>
  <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage/images"/>
  <label>foo@ns:trunk-stage</label>
  <name>NewStage</name>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <name>chater-foo</name>
    <short_name>chater-foo</short_name>
  </project>
  <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
    <name>trunk</name>
  </project_branch>
  <promotable>false</promotable>
  <stage_id>12</stage_id>
</stage>
""".strip()

# <imageDefinitions> camelCase only for compatibility reasons, change back to underscore ASAP
project_branch_xml = """\
<project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
  <branch_id>5</branch_id>
  <description/>
  <label>chater-foo.eng.rpath.com@rpath:chater-foo-trunk</label>
  <name>trunk</name>
  <namespace>rpath</namespace>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <name>chater-foo</name>
    <short_name>chater-foo</short_name>
  </project>
  <project_branch_stages id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages"/>
  <source_group>group-foo-appliance</source_group>
  <imageDefinitions id="http://testserver/api/products/chater-foo/versions/trunk/imageDefinitions"/>
  <image_type_definitions id="http://testserver/api/products/chater-foo/versions/trunk/imageTypeDefinitions"/>
</project_branch>"""

project_image_post_xml = """\
  <image>
    <project id="http://testserver/api/v1/projects/chater-foo">
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
    <build_type>image-test-build-type</build_type>
    <time_created>1</time_created>
  </image>
"""

project_branch_stages_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<project_branch_stages count="4" next_page="" num_pages="1" previous_page="" full_collection="" end_index="3" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development">
    <stage_id>10</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>Development</name>
    <repository_api id="http://testserver/repos/chater-foo/api"/>
    <label>foo@ns:trunk-devel</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <groups promote_href="https://testserver/api/products/chater-foo/versions/trunk/stages/Development" href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-devel"/>
    <created_date>2011-10-12T21:22:24.206535+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/QA">
    <stage_id>11</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>QA</name>
    <repository_api id="http://testserver/repos/chater-foo/api"/>
    <label>foo@ns:trunk-qa</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <groups promote_href="https://testserver/api/products/chater-foo/versions/trunk/stages/QA" href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-qa"/>
    <created_date>2011-10-12T21:22:24.209524+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/QA/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage">
    <stage_id>12</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>Stage</name>
    <repository_api id="http://testserver/repos/chater-foo/api"/>
    <label>foo@ns:trunk-stage</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <groups promote_href="https://testserver/api/products/chater-foo/versions/trunk/stages/Stage" href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-stage"/>
    <created_date>2011-10-12T21:22:24.212755+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Release">
    <stage_id>13</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>Release</name>
    <repository_api id="http://testserver/repos/chater-foo/api"/>
    <label>foo@ns:trunk</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <groups promote_href="https://testserver/api/products/chater-foo/versions/trunk/stages/Release" href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk"/>
    <created_date>2011-10-12T21:22:24.215180+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Release/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
</project_branch_stages>
""".strip()

project_branch_stage_images_post_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image>
    <status>-1</status>
    <stage_name>Development</stage_name>
    <time_updated></time_updated>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <updated_by></updated_by>
    <trove_version></trove_version>
    <created_by></created_by>
    <trove_flavor></trove_flavor>
    <trove_last_changed></trove_last_changed>
    <name>image-1</name>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <job_uuid></job_uuid>
    <output_trove></output_trove>
    <time_created></time_created>
    <release></release>
    <build_count>0</build_count>
    <status_message></status_message>
    <build_type>10</build_type>
    <trove_name></trove_name>
    <description>image-1</description>
</image>
""".strip()

project_branch_stage_images_post_return_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<images count="1" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images" end_index="0" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images;start_index=0;limit=10" start_index="0">
  <image>
    <status>-1</status>
    <stage_name>Development</stage_name>
    <time_updated></time_updated>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <updated_by></updated_by>
    <trove_version></trove_version>
    <created_by></created_by>
    <trove_flavor></trove_flavor>
    <trove_last_changed></trove_last_changed>
    <name>image-1</name>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <image_id>2</image_id>
    <job_uuid></job_uuid>
    <output_trove></output_trove>
    <time_created></time_created>
    <release></release>
    <build_count>0</build_count>
    <status_message></status_message>
    <build_type>10</build_type>
    <trove_name></trove_name>
    <description>image-1</description>
  </image>
</images>
""".strip()

releases_by_project_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<releases count="2" next_page="" num_pages="1" previous_page="" full_collection="http://testserver/api/v1/releases" end_index="1" limit="10" order_by="" per_page="10" filter_by="" id="http://testserver/api/v1/releases;start_index=0;limit=10" start_index="0">
  <release id="http://testserver/api/v1/releases/1">
    <release_id>1</release_id>
    <name>release1</name>
    <description>description1</description>
    <time_created></time_created>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <should_mirror>0</should_mirror>
    <published_by></published_by>
    <time_updated></time_updated>
    <created_by></created_by>
    <version>releaseVersion1</version>
    <published>False</published>
    <images>
      <image id="http://testserver/api/v1/images/2">
        <files/>
        <trove_last_changed></trove_last_changed>
        <updated_by></updated_by>
        <trailing_version>1-1-1</trailing_version>
        <num_image_files>0</num_image_files>
        <image_type id="http://testserver/api/v1/image_types/10">
          <description>VHD for Microsoft (R) Hyper-V</description>
          <name>Microsoft (R) Hyper-V</name>
          <key>VIRTUAL_PC_IMAGE</key>
          <image_type_id>10</image_type_id>
        </image_type>
        <build_log id="http://testserver/api/v1/images/2/build_log"/>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <created_by></created_by>
        <status_message></status_message>
        <trove_name>troveName1</trove_name>
        <status>-1</status>
        <stage_name>stage1</stage_name>
        <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
          <name>trunk</name>
        </project_branch>
        <description>image-1</description>
        <image_id>2</image_id>
        <time_created></time_created>
        <time_updated></time_updated>
        <name>image-1</name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
        <released>True</released>
        <project id="http://testserver/api/v1/projects/chater-foo">
          <domain_name>eng.rpath.com</domain_name>
          <short_name>chater-foo</short_name>
          <name>chater-foo</name>
        </project>
        <output_trove></output_trove>
        <architecture>x86</architecture>
        <base_image/>
        <release id="http://testserver/api/v1/releases/1"/>
        <image_count>1</image_count>
        <job_uuid>1</job_uuid>
      </image>
    </images>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by></updated_by>
  </release>
  <release id="http://testserver/api/v1/releases/2">
    <release_id>2</release_id>
    <name>release2</name>
    <description>description2</description>
    <time_created></time_created>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <should_mirror>0</should_mirror>
    <published_by></published_by>
    <time_updated></time_updated>
    <created_by></created_by>
    <version>releaseVersion2</version>
    <published>False</published>
    <images>
      <image id="http://testserver/api/v1/images/3">
        <files/>
        <trove_last_changed></trove_last_changed>
        <updated_by></updated_by>
        <trailing_version>1-2-1</trailing_version>
        <num_image_files>0</num_image_files>
        <image_type id="http://testserver/api/v1/image_types/10">
          <description>VHD for Microsoft (R) Hyper-V</description>
          <name>Microsoft (R) Hyper-V</name>
          <key>VIRTUAL_PC_IMAGE</key>
          <image_type_id>10</image_type_id>
        </image_type>
        <build_log id="http://testserver/api/v1/images/3/build_log"/>
        <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
        <created_by></created_by>
        <status_message></status_message>
        <trove_name>troveName2</trove_name>
        <status>-1</status>
        <stage_name>stage2</stage_name>
        <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
          <name>trunk</name>
        </project_branch>
        <description>image-2</description>
        <image_id>3</image_id>
        <time_created></time_created>
        <time_updated></time_updated>
        <name>image-2</name>
        <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-2-1</trove_version>
        <released>True</released>
        <project id="http://testserver/api/v1/projects/chater-foo">
          <domain_name>eng.rpath.com</domain_name>
          <short_name>chater-foo</short_name>
          <name>chater-foo</name>
        </project>
        <output_trove></output_trove>
        <architecture>x86</architecture>
        <base_image/>
        <release id="http://testserver/api/v1/releases/2"/>
        <image_count>1</image_count>
        <job_uuid>1</job_uuid>
      </image>
    </images>
    <time_mirrored></time_mirrored>
    <time_published></time_published>
    <updated_by></updated_by>
  </release>
</releases>
""".strip()

release_by_project_post_xml = \
"""
<release>
  <name>release2002</name>
  <description>description2002</description>
  <project id="http://testserver/api/v1/projects/foo"/>
  <should_mirror>0</should_mirror>
  <version>releaseVersion2002</version>
</release>
"""

image_by_release_get_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<images count="1" next_page="" num_pages="1" previous_page="" full_collection="" end_index="0" limit="10" order_by="" per_page="10" filter_by="" start_index="0">
  <image id="http://testserver/api/v1/images/2">
    <files/>
    <trove_last_changed></trove_last_changed>
    <updated_by></updated_by>
    <trailing_version>1-1-1</trailing_version>
    <num_image_files>0</num_image_files>
    <image_type id="http://testserver/api/v1/image_types/10">
      <description>VHD for Microsoft (R) Hyper-V</description>
      <name>Microsoft (R) Hyper-V</name>
      <key>VIRTUAL_PC_IMAGE</key>
      <image_type_id>10</image_type_id>
    </image_type>
    <build_log id="http://testserver/api/v1/images/2/build_log"/>
    <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
    <created_by></created_by>
    <status_message></status_message>
    <trove_name>troveName1</trove_name>
    <status>-1</status>
    <stage_name>stage1</stage_name>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <description>image-1</description>
    <image_id>2</image_id>
    <time_created></time_created>
    <time_updated></time_updated>
    <name>image-1</name>
    <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
    <released>True</released>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <output_trove></output_trove>
    <architecture>x86</architecture>
    <base_image/>
    <release id="http://testserver/api/v1/releases/1"/>
    <image_count>1</image_count>
    <job_uuid>1</job_uuid>
  </image>
</images>
""".strip()

image_by_release_post_xml = \
"""
<image>
  <trailing_version>1-1-1</trailing_version>
  <num_image_files>0</num_image_files>
  <image_type id="http://testserver/api/v1/image_types/10">
    <description>VHD for Microsoft (R) Hyper-V</description>
    <name>Microsoft (R) Hyper-V</name>
    <key>VIRTUAL_PC_IMAGE</key>
    <image_type_id>10</image_type_id>
  </image_type>
  <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
  <trove_name>troveName1</trove_name>
  <status>-1</status>
  <stage_name>image by release</stage_name>
  <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk" />
  <description>image-1</description>
  <name>image-2000</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
  <released>True</released>
  <project id="http://testserver/api/v1/projects/chater-foo" />
  <architecture>x86</architecture>
  <base_image/>
  <image_count>1</image_count>
  <job_uuid>1</job_uuid>
</image>
"""
empty_projects="""
<projects count="0" end_index="0" filter_by="" full_collection="http://testserver/api/v1/query_sets/10/all" id="http://testserver/api/v1/query_sets/10/all;start_index=0;limit=10" limit="10" next_page="" num_pages="1" order_by="" per_page="10" previous_page="" start_index="0"/>
"""

image_by_release_post_result_xml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<image id="http://testserver/api/v1/images/4">
  <files/>
  <trove_last_changed></trove_last_changed>
  <updated_by></updated_by>
  <trailing_version>1-1-1</trailing_version>
  <num_image_files>0</num_image_files>
  <image_type id="http://testserver/api/v1/image_types/10">
    <description></description>
    <name></name>
    <key></key>
    <image_type_id>10</image_type_id>
  </image_type>
  <build_log id="http://testserver/api/v1/images/4/build_log"/>
  <trove_flavor>1#x86:i486:i586:i686|5#use:~!xen</trove_flavor>
  <created_by id="http://testserver/api/v1/users/2002"/>
  <status_message></status_message>
  <trove_name>troveName1</trove_name>
  <status>-1</status>
  <stage_name>image by release</stage_name>
  <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
    <name>trunk</name>
  </project_branch>
  <description>image-1</description>
  <image_id>4</image_id>
  <time_created>2011-10-13 13:48:41.901060+00:00</time_created>
  <time_updated>2011-10-13 13:48:41.901060+00:00</time_updated>
  <name>image-2000</name>
  <trove_version>/cydonia.eng.rpath.com@rpath:cydonia-1-devel/1317221453.365:1-1-1</trove_version>
  <released>False</released>
  <project id="http://testserver/api/v1/projects/chater-foo">
    <domain_name>eng.rpath.com</domain_name>
    <short_name>chater-foo</short_name>
    <name>chater-foo</name>
  </project>
  <output_trove></output_trove>
  <architecture>x86</architecture>
  <base_image/>
  <release></release>
  <image_count>0</image_count>
  <job_uuid>1</job_uuid>
</image>
""".strip()
