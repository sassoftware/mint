XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>Windows WIM Configuration</displayName>
        <descriptions>
            <desc>Windows WIM Configuration</desc>
        </descriptions>
    </metadata>

    <dataFields>
        <field>
            <name>displayName</name>
            <help lang="en_US">@Help_image_name@</help>
            <required>true</required>
            <descriptions>
                <desc>Image name</desc>
            </descriptions>
            <prompt>
                <desc>Example: Example WIM Image</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>container.options.baseFileName</name>
            <help lang="en_US">@Help_image_filename@</help>
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
