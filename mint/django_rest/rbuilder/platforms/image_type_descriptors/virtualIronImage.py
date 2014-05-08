XML = """<?xml version='1.0' encoding='UTF-8'?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
    <metadata>
        <displayName>Virtual Iron Image Configuration</displayName>
        <descriptions>
            <desc>Virtual Iron Image Configuration</desc>
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
            <name>options.installLabelPath</name>
            <descriptions>
                <desc>Conary installLabelPath</desc>
            </descriptions>
            <help href="@Help_conary_installlabelpath@"/>
            <type>str</type>
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
            <constraints>
                <range>
                    <min>16</min>
                </range>
            </constraints>
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
            <name>options.vhdDiskType</name>
            <descriptions>
                <desc>VHD Hard Disk Type</desc>
            </descriptions>
            <help href="@Help_vhd_disk_type@"/>
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
            <required>true</required>
        </field>
    </dataFields>
</descriptor>"""
