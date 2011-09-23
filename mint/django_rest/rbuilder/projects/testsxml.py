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
    <project id="http://127.0.0.1:8000/api/v1/projects/foo"/>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
    <platform id=""/>
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
  <systems/>
</project_branch_stage>"""

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
    <label>foo@ns:trunk-devel</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <systems/>
    <groups href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-devel"/>
    <created_date>2011-09-13T21:49:24.421095+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Development/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/QA">
    <stage_id>11</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>QA</name>
    <label>foo@ns:trunk-qa</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <systems/>
    <groups href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-qa"/>
    <created_date>2011-09-13T21:49:24.423607+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/QA/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage">
    <stage_id>12</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>Stage</name>
    <label>foo@ns:trunk-stage</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <systems/>
    <groups href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk-stage"/>
    <created_date>2011-09-13T21:49:24.426203+00:00</created_date>
    <images id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Stage/images"/>
    <promotable>false</promotable>
  </project_branch_stage>
  <project_branch_stage id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk/project_branch_stages/Release">
    <stage_id>13</stage_id>
    <project_branch id="http://testserver/api/v1/projects/chater-foo/project_branches/chater-foo.eng.rpath.com@rpath:chater-foo-trunk">
      <name>trunk</name>
    </project_branch>
    <name>Release</name>
    <label>foo@ns:trunk</label>
    <project id="http://testserver/api/v1/projects/chater-foo">
      <domain_name>eng.rpath.com</domain_name>
      <short_name>chater-foo</short_name>
      <name>chater-foo</name>
    </project>
    <systems/>
    <groups href="https://testserver/api/products/chater-foo/repos/search?type=group&amp;label=foo@ns:trunk"/>
    <created_date>2011-09-13T21:49:24.429069+00:00</created_date>
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