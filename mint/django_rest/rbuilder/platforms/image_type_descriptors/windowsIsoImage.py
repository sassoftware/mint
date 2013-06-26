XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>Windows ISO Configuration</displayName>
        <descriptions>
            <desc>Windows ISO Configuration</desc>
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
            <name>options.platformIsoKitTrove</name>
            <descriptions>
                <desc>platform-isokit</desc>
            </descriptions>
            <help href="@Help_platform_isokit@"/>
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
            <name>options.baseFileName</name>
            <descriptions>
                <desc>Image filename</desc>
            </descriptions>
            <help href="@Help_image_filename@"/>
            <type>str</type>
            <required>false</required>
        </field>
    </dataFields>
</descriptor>"""
