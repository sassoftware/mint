XML="""<createApplianceDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd"
  >
    <metadata>
        <displayName>Installable CD/DVD Image Configuration</displayName>
        <descriptions>
            <desc>Installable CD/DVD Image Configuration</desc>
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
                <desc>Example: Example System Image</desc>
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
            <name>options.bugsUrl</name>
            <help lang="en_US">@Help_bug_report_url@</help>
            <required>false</required>
            <descriptions>
                <desc>Bug Report URL</desc>
            </descriptions>
            <prompt>
                <desc>Example: http://issues.example.com</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>options.betaNag</name>
            <help lang="en_US">@Help_beta@</help>
            <required>false</required>
            <descriptions>
                <desc>Beta?</desc>
            </descriptions>
            <prompt>
                <desc>Check to have the installer indicate that the image is a beta.</desc>
            </prompt>
            <type>bool</type>
            <default></default>
        </field>
        <field>
            <name>options.showMediaCheck</name>
            <help lang="en_US">@Help_cd_verify@</help>
            <required>false</required>
            <descriptions>
                <desc>CD verify?</desc>
            </descriptions>
            <prompt>
                <desc>Check to prompt the user to verify CD/DVD images during install.</desc>
            </prompt>
            <type>bool</type>
            <default></default>
        </field>

        <field>
            <name>options.anacondaTemplatesTrove</name>
            <help lang="en_US">@Help_anaconda_templates@</help>
            <required>false</required>
            <descriptions>
                <desc>anaconda-templates</desc>
            </descriptions>
            <prompt>
                <desc>Example: anaconda-templates=/example.rpath.org@corp:example-1/1.1-2-1</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>options.anacondaCustomTrove</name>
            <help lang="en_US">@Help_anaconda_custom@</help>
            <required>false</required>
            <descriptions>
                <desc>anaconda-custom</desc>
            </descriptions>
            <prompt>
                <desc>Example: anaconda-custom=/example.rpath.org@corp:example-1/1.1-2-1</desc>
            </prompt>
            <type>str</type>
            <default></default>
        </field>
        <field>
            <name>options.mediaTemplateTrove</name>
            <help lang="en_US">@Help_media_template@</help>
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
            <name>options.maxIsoSize</name>
            <help lang="en_US">@Help_iso_size@</help>
            <required>true</required>
            <descriptions>
                <desc>ISO Size</desc>
            </descriptions>
            <prompt>
                <desc>Select the ISO size needed for your install media.</desc>
            </prompt>
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
            <default></default>
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
