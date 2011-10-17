XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>Windows ISO Configuration</displayName>
        <descriptions>
            <desc>Windows ISO Configuration</desc>
        </descriptions>
    </metadata>

    <dataFields>
        <field>
            <name>displayName</name>
            <help lang="en_US" href="@Help_image_name@"/>
            <required>true</required>
            <descriptions>
                <desc>Image name</desc>
            </descriptions>
            <prompt>
                <desc>Example: Example ISO Image</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>

        <field>
            <name>options.platformIsoKitTrove</name>
            <help lang="en_US" href="@Help_platform_isokit@"/>
            <required>false</required>
            <descriptions>
                <desc>platform-isokit</desc>
            </descriptions>
            <prompt>
                <desc>Example: platform-isokit=/example.rpath.org@corp:example-1/1.1-2-1</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>options.mediaTemplateTrove</name>
            <help lang="en_US" href="@Help_media_template@"/>
            <required>false</required>
            <descriptions>
                <desc>media-template</desc>
            </descriptions>
            <prompt>
                <desc>Example: media-template=/example.rpath.org@corp:example-1/1.1-2-1</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        
        <field>
            <name>options.baseFileName</name>
            <help lang="en_US" href="@Help_image_filename@"/>
            <required>false</required>
            <descriptions>
                <desc>Image filename</desc>
            </descriptions>
            <prompt>
                <desc>Example: example-1.0-x86_64 (replaces name-version-arch)</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
    </dataFields>
</createApplianceDescriptor>"""
