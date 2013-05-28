XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>VMware ESX Server Image Configuration</displayName>
        <descriptions>
            <desc>VMware ESX Server Image Configuration</desc>
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
            <default/>
            <required>true</required>
        </field>
        <field>
            <name>options.baseFileName</name>
            <descriptions>
                <desc>Image filename</desc>
            </descriptions>
            <help href="@Help_image_filename@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.installLabelPath</name>
            <descriptions>
                <desc>Conary installLabelPath</desc>
            </descriptions>
            <help href="@Help_conary_installlabelpath@"/>
            <type>str</type>
            <default/>
            <required>false</required>
        </field>
        <field>
            <name>options.freespace</name>
            <descriptions>
                <desc>Free space</desc>
            </descriptions>
            <help href="@Help_image_freespace@"/>
            <type>int</type>
            <default>256</default>
            <required>false</required>
        </field>
        <field>
            <name>options.swapSize</name>
            <descriptions>
                <desc>Swap space</desc>
            </descriptions>
            <help href="@Help_image_swapspace@"/>
            <type>int</type>
            <default>512</default>
            <required>false</required>
        </field>
        <field>
            <name>options.vmCPUs</name>
            <descriptions>
                <desc>CPUs</desc>
            </descriptions>
            <help href="@Help_image_cpus@"/>
            <type>int</type>
            <default>1</default>
            <required>false</required>
        </field>
        <field>
            <name>options.vmMemory</name>
            <descriptions>
                <desc>RAM</desc>
            </descriptions>
            <help href="@Help_image_ram@"/>
            <type>int</type>
            <default>1024</default>
            <required>false</required>
        </field>
        <field>
            <name>options.autoResolve</name>
            <descriptions>
                <desc>Autoinstall Dependencies</desc>
            </descriptions>
            <help href="@Help_resolve_dependencies@"/>
            <type>bool</type>
            <default>false</default>
            <required>false</required>
        </field>
        <field>
            <name>options.natNetworking</name>
            <descriptions>
                <desc>Use NAT?</desc>
            </descriptions>
            <help href="@Help_image_use_nat@"/>
            <type>bool</type>
            <default>true</default>
            <hidden>true</hidden>
        </field>
        <field>
            <name>options.allowSnapshots</name>
            <descriptions>
                <desc>Allow snapshots?</desc>
            </descriptions>
            <help href="@Help_allow_snapshots@"/>
            <type>bool</type>
            <default>true</default>
            <hidden>true</hidden>
        </field>
        <field>
            <name>options.buildOVF10</name>
            <descriptions>
                <desc>Generate in OVF 1.0?</desc>
            </descriptions>
            <help href="@Help_build_ovf_1_0@"/>
            <type>bool</type>
            <default>true</default>
            <hidden>true</hidden>
        </field>
    </dataFields>
</descriptor>"""
