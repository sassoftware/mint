XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>TAR File Image Configuration</displayName>
        <descriptions>
            <desc>TAR File Image Configuration</desc>
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
            <hidden>true</hidden>
        </field>
    </dataFields>
</descriptor>"""
