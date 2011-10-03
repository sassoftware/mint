XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>VMware ESX Server Image Configuration</displayName>
        <descriptions>
            <desc>VMware ESX Server Image Configuration</desc>
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
                <desc>Example: Example System Image for VMware ESX Server</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>options.baseFileName</name>
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
        <field>
            <name>options.installLabelPath</name>
            <help lang="en_US">@Help_conary_installlabelpath@</help>
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
            <help lang="en_US">@Help_image_freespace@</help>
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
            <help lang="en_US">@Help_image_swapspace@</help>
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
            <name>options.vmMemory</name>
            <help lang="en_US">@Help_image_ram@</help>
            <required>false</required>
            <descriptions>
                <desc>RAM</desc>
            </descriptions>
            <prompt>
                <desc>Example: 512</desc>
            </prompt>
            <type>int</type>
            <default>512</default>
        </field>
                
        <field>
            <name>options.autoResolve</name>
            <help lang="en_US">@Help_resolve_dependencies@</help>
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
            <name>options.natNetworking</name>
            <help lang="en_US">@Help_image_use_nat@</help>
            <required>false</required>
            <descriptions>
                <desc>Use NAT?</desc>
            </descriptions>
            <prompt>
                <desc>Check if the VM should use NAT instead of bridged networking.</desc>
            </prompt>
            <type>bool</type>
            <default>true</default>
        </field>

        <field>
            <name>options.allowSnapshots</name>
            <help lang="en_US">@Help_allow_snapshots@</help>
            <required>false</required>
            <descriptions>
                <desc>Allow snapshots?</desc>
            </descriptions>
            <prompt>
                <desc>Check if the VM should allow the user to take snapshots of the system.</desc>
            </prompt>
            <type>bool</type>
            <default>true</default>
        </field>

        <field>
            <name>options.buildOVF10</name>
            <help lang="en_US">@Help_build_ovf_1_0@</help>
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
