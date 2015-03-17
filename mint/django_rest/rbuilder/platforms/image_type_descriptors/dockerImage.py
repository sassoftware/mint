XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>Docker Image Configuration</displayName>
        <descriptions>
            <desc>Docker Image Configuration</desc>
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
            <name>options.dockerfile</name>
            <descriptions>
                <desc>Dockerfile contents</desc>
            </descriptions>
            <help href="@Help_dockerfile@"/>
            <type>str</type>
            <constraints>
                <descriptions>
                    <desc>Field must contain between 0 and 16384 characters</desc>
                </descriptions>
                <length>16384</length>
            </constraints>
            <required>false</required>
        </field>
    </dataFields>
</descriptor>"""
