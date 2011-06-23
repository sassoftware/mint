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
    <hostname>test-project.eng.rpath.com</hostname>
    <namespace>rpath</namespace>
    <domain_name>eng.rpath.com</domain_name>
    <hidden>0</hidden>
    <description>test project description</description>
    <backup_external>0</backup_external>
    <repository_hostname>test-project.eng.rpath.com</repository_hostname>
    <external>0</external>
    <name>test-project</name>
  </project>
"""

project_put_xml = """\
  <project>
    <short_name>chater-foo</short_name>
    <description>updated description</description>
  </project>
"""

project_version_post_no_project_xml = """\
  <project_branch>
    <project_short_name>foo</project_short_name>
    <project_name>foo appliance</project_name>
    <project_type>Appliance</project_type>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
  </project_branch>
"""

project_version_post_with_project_xml = """\
  <project_branch>
    <project id="http://127.0.0.1:8000/api/v1/projects/foo"/>
    <project_short_name>foo</project_short_name>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
  </project_branch>
"""

project_version_post_with_project_no_auth_xml = """\
  <project_branch>
    <project id="http://127.0.0.1:8000/api/v1/projects/test-project"/>
    <project_short_name>foo</project_short_name>
    <description>1</description>
    <namespace>rpath</namespace>
    <name>42</name>
  </project_branch>
"""

project_version_put_xml = """\
  <project_branch id="http://127.0.0.1:8000/api/v1/project_branches/2">
    <description>updated description</description>
  </project_branch>
"""
