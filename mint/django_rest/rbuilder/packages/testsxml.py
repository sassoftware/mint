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

package_version_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
  <package_version>
    <name>3.0</name>
    <license>Apache</license>
    <package id="http://127.0.0.1:8000/api/packages/1"/>
    <consumable>true</consumable>
  </package_version>
"""

package_version_url_post_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<package_version_url>
  <url>http://httpd.apache.org/download.cgi#apache30</url>
  <package_version id="http://127.0.0.1:8000/api/package_versions/1"/>
</package_version_url>
"""
