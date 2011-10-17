XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>VHD Image Configuration for Microsoft Hyper-V</displayName>
        <descriptions>
            <desc>VHD Image Configuration for Microsoft Hyper-V</desc>
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
                <desc>Example: Example System Image for Hyper-V</desc>
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
                <desc>Exmaple: rus.example.com@corp:example-1 (leave blank for default)</desc>
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
            <name>options.vhdDiskType</name>
            <help lang="en_US" href="@Help_vhd_disk_type@"/>
            <required>true</required>
            <descriptions>
                <desc>VHD Hard Disk Type</desc>
            </descriptions>
            <prompt>
                <desc>Select the VHD hard disk type for this image.</desc>
            </prompt>
            <enumeratedType>
            
              <describedValue>
                <descriptions>
                  <desc>Dynamic image</desc>
                </descriptions>
                <key>dynamic</key>
              </describedValue>
              
              <describedValue>
                <descriptions>
                  <desc>Difference image</desc>
                </descriptions>
                <key>difference</key>
              </describedValue>
             
              <describedValue>
                <descriptions>
                  <desc>Fixed image</desc>
                </descriptions>
                <key>fixed</key>
              </describedValue>
              
             </enumeratedType>
            <default>dynamic</default>
        </field>   
        
    </dataFields>
</createApplianceDescriptor>"""
