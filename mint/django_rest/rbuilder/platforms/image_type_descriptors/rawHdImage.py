XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>Parallels, QEMU (Raw Hard Disk) Image Configuration</displayName>
        <descriptions>
            <desc>Parallels, QEMU, (Raw Hard Disk) Image Configuration</desc>
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
                <desc>Example: Example System Image</desc>
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
        <field>
            <name>options.installLabelPath</name>
            <help lang="en_US" href="@Help_conary_installlabelpath@"/>
            <required>false</required>
            <descriptions>
                <desc>Conary installLabelPath</desc>
            </descriptions>
            <prompt>
                <desc>Example: rus.example.com@corp:example-1 (leave blank for default)</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>

        <field>
            <name>options.freespace</name>
            <help lang="en_US" href="@Help_image_freespace@"/>
            <required>false</required>
            <descriptions>
                <desc>Free space</desc>
            </descriptions>
            <prompt>
                <desc>Example: 256</desc>
            </prompt>
            <type>int</type>
            <default>256</default>
        </field>


        <field>
            <name>options.swapSize</name>
            <help lang="en_US" href="@Help_image_swapspace@"/>
            <required>false</required>
            <descriptions>
                <desc>Swap space</desc>
            </descriptions>
            <prompt>
                <desc>Example: 512</desc>
            </prompt>
            <type>int</type>
            <default>512</default>
        </field>
        
        <field>
            <name>options.autoResolve</name>
            <help lang="en_US" href="@Help_resolve_dependencies@"/>
            <required>false</required>
            <descriptions>
                <desc>Autoinstall Dependencies</desc>
            </descriptions>
            <prompt>
                <desc>Check to automatically install required dependencies during updates.</desc>
            </prompt>
            <type>bool</type>
            <default>false</default>
        </field>

        <field>
            <name>options.buildOVF10</name>
            <help lang="en_US" href="@Help_build_ovf_1_0@"/>
            <required>false</required>
            <descriptions>
                <desc>Generate in OVF 1.0?</desc>
            </descriptions>
            <prompt>
                <desc>Check to generate the image in OVF 1.0 format.</desc>
            </prompt>
            <type>bool</type>
            <default>false</default>
        </field>

    </dataFields>
</createApplianceDescriptor>"""
