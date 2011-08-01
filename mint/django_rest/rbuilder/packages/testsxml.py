#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

package_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<package> 
  <name>conary</name>
  <description>Conary Package Manager</description>
</package>
"""

package_put_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<package>
  <name>Apache</name>
  <description>Apache Renamed</description>
</package>
"""

package_version_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
  <package_version>
    <name>3.0</name>
    <description>3.0</description>
    <license>Apache</license>
    <package id="http://127.0.0.1:8000/api/v1/packages/1"/>
    <consumable>true</consumable>
  </package_version>
"""

package_version_put_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
  <package_version>
    <name>3.1</name>
    <license>Apache</license>
    <package id="http://127.0.0.1:8000/api/v1/packages/1"/>
    <consumable>false</consumable>
  </package_version>
"""

package_version_url_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<package_version_url>
  <url>http://httpd.apache.org/download.cgi#apache30</url>
  <package_version id="http://127.0.0.1:8000/api/v1/package_versions/1"/>
</package_version_url>
"""

package_version_url_post_xml2 = """\
<?xml version='1.0' encoding='UTF-8'?>
<package_version_url>
  <url>http://httpd.apache.org/download.cgi#apache31</url>
  <package_version id="http://127.0.0.1:8000/api/v1/package_versions/1"/>
</package_version_url>
"""

package_version_commit_job_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
  <package_version_job>
    <package_version id="http://127.0.0.1:8000/api/v1/package_versions/6"/>
    <package_action_type id="http://127.0.0.1:8000/api/v1/package_action_types/1"/>
    <job_data>
        <commit_label>testlabel.eng.rpath.com@rpath:test-1-devel</commit_label> 
    </job_data>
  </package_version_job>
"""
