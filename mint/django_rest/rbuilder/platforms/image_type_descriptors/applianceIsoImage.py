XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>Appliance Installable ISO Configuration</displayName>
        <descriptions>
            <desc>Appliance Installable ISO Configuration</desc>
        </descriptions>
    </metadata>
    <dataFields>
        <field>
            <name>displayName</name>
            <descriptions>
                <desc>Image name</desc>
            </descriptions>
            <help lang="en_US" href="@Help_image_name@"/>
            <type>str</type>
            <default/>
            <required>true</required>
        </field>
        <field>
            <name>options.bugsUrl</name>
            <descriptions>
                <desc>Bug Report URL</desc>
            </descriptions>
            <help lang="en_US" href="@Help_bug_report_url@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.betaNag</name>
            <descriptions>
                <desc>Beta?</desc>
            </descriptions>
            <help lang="en_US" href="@Help_beta@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.showMediaCheck</name>
            <descriptions>
                <desc>CD verify?</desc>
            </descriptions>
            <help lang="en_US" href="@Help_cd_verify@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.anacondaTemplatesTrove</name>
            <descriptions>
                <desc>anaconda-templates</desc>
            </descriptions>
            <help lang="en_US" href="@Help_anaconda_templates@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.anacondaCustomTrove</name>
            <descriptions>
                <desc>anaconda-custom</desc>
            </descriptions>
            <help lang="en_US" href="@Help_anaconda_custom@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.mediaTemplateTrove</name>
            <descriptions>
                <desc>media-template</desc>
            </descriptions>
            <help lang="en_US" href="@Help_media_template@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.baseFileName</name>
            <descriptions>
                <desc>Image filename</desc>
            </descriptions>
            <help lang="en_US" href="@Help_image_filename@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.installLabelPath</name>
            <descriptions>
                <desc>Conary installLabelPath</desc>
            </descriptions>
            <help lang="en_US" href="@Help_conary_installlabelpath@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.autoResolve</name>
            <descriptions>
                <desc>Autoinstall Dependencies</desc>
            </descriptions>
            <help lang="en_US" href="@Help_resolve_dependencies@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.buildOVF10</name>
            <descriptions>
                <desc>Generate in OVF 1.0?</desc>
            </descriptions>
            <help lang="en_US" href="@Help_build_ovf_1_0@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
    </dataFields>
</descriptor>"""
