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
        <displayName>Installable CD/DVD Image Configuration</displayName>
        <descriptions>
            <desc>Installable CD/DVD Image Configuration</desc>
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
            <name>options.bugsUrl</name>
            <descriptions>
                <desc>Bug Report URL</desc>
            </descriptions>
            <help href="@Help_bug_report_url@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.betaNag</name>
            <descriptions>
                <desc>Beta?</desc>
            </descriptions>
            <help href="@Help_beta@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.showMediaCheck</name>
            <descriptions>
                <desc>CD verify?</desc>
            </descriptions>
            <help href="@Help_cd_verify@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.anacondaTemplatesTrove</name>
            <descriptions>
                <desc>anaconda-templates</desc>
            </descriptions>
            <help href="@Help_anaconda_templates@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.anacondaCustomTrove</name>
            <descriptions>
                <desc>anaconda-custom</desc>
            </descriptions>
            <help href="@Help_anaconda_custom@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.mediaTemplateTrove</name>
            <descriptions>
                <desc>media-template</desc>
            </descriptions>
            <help href="@Help_media_template@"/>
            <type>str</type>
            <required>false</required>
        </field>
        <field>
            <name>options.maxIsoSize</name>
            <descriptions>
                <desc>ISO Size</desc>
            </descriptions>
            <help href="@Help_iso_size@"/>
            <enumeratedType>
                <describedValue>
                    <descriptions>
                        <desc>CD: 650 MB</desc>
                    </descriptions>
                    <key>681574400</key>
                </describedValue>
                <describedValue>
                    <descriptions>
                        <desc>CD: 700 MB</desc>
                    </descriptions>
                    <key>734003200</key>
                </describedValue>
                <describedValue>
                    <descriptions>
                        <desc>DVD: 4.7 GB</desc>
                    </descriptions>
                    <key>4700000000</key>
                </describedValue>
                <describedValue>
                    <descriptions>
                        <desc>DVD: 8.5 GB</desc>
                    </descriptions>
                    <key>8500000000</key>
                </describedValue>
            </enumeratedType>
            <required>true</required>
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
