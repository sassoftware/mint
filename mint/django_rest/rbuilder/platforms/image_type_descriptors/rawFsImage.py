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


XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>Mountable Filesystem Image Configuration</displayName>
        <descriptions>
            <desc>Mountable Filesystem Image Configuration</desc>
        </descriptions>
    </metadata>
    <dataFields>
        <field>
            <name>displayName</name>
            <descriptions>
                <desc>Image name</desc>
            </descriptions>
            <help href="@Help_image_name@"/>
            <type>str</type>
            <required>true</required>
        </field>
        <field>
            <name>options.baseFileName</name>
            <descriptions>
                <desc>Image filename</desc>
            </descriptions>
            <help href="@Help_image_filename@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.installLabelPath</name>
            <descriptions>
                <desc>Conary installLabelPath</desc>
            </descriptions>
            <help href="@Help_conary_installlabelpath@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.freespace</name>
            <descriptions>
                <desc>Free space</desc>
            </descriptions>
            <help href="@Help_image_freespace@"/>
            <type>int</type>
            <default>256</default>
            <constraints>
                <range>
                    <min>16</min>
                </range>
            </constraints>
            <required>false</required>
        </field>
        <field>
            <name>options.swapSize</name>
            <descriptions>
                <desc>Swap space</desc>
            </descriptions>
            <help href="@Help_image_swapspace@"/>
            <type>int</type>
            <default>512</default>
            <constraints>
                <range>
                    <min>16</min>
                </range>
            </constraints>
            <required>false</required>
        </field>
        <field>
            <name>options.autoResolve</name>
            <descriptions>
                <desc>Autoinstall Dependencies</desc>
            </descriptions>
            <help href="@Help_resolve_dependencies@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.buildOVF10</name>
            <descriptions>
                <desc>Generate in OVF 1.0?</desc>
            </descriptions>
            <help href="@Help_build_ovf_1_0@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
    </dataFields>
</descriptor>"""
