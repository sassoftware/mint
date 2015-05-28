#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


platformsXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/v1/platforms/5">
    <platform_id>5</platform_id>
    <platform_name>Platform5</platform_name>
    <label>Platform5label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="1"/>
  </platform>
  <platform id="http://localhost:8000/api/v1/platforms/6">
    <platform_id>6</platform_id>
    <platform_name>Platform6</platform_name>
    <label>Platform6label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="2"/>
  </platform>
  <platform id="http://localhost:8000/api/v1/platforms/7">
    <platform_id>7</platform_id>
    <platform_name>Platform7</platform_name>
    <label>Platform7label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="3"/>
  </platform>
</platforms>
""".strip()

platformPOSTXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platform>
    <platform_name>Platform5</platform_name>
    <label>PlatformMyPlatformLabel2</label>
    <mode>manual</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <projects id="http://localhost:8000/api/v1/projects/morbeef" />
</platform>
""".strip()

#Prath
platformPUTXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platform>
    <label>PlatformChanged</label>
    <platform_name>Platform Name Changed</platform_name>
    <mode>auto</mode>
    <enabled>0</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
</platform>
""".strip()


#Prath
platformVersionPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformVersion>
  <name>PlatformVersionPostTest</name>
  <version>Post</version>
  <revision>Post</revision>
  <label>PlatformVersionPostTest</label>
  <ordering>PlatformVersionPostTest</ordering>
</platformVersion>
"""
