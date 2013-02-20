XML = """\
<?xml version="1.1" encoding="UTF-8"?>
<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.1.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd">
  <metadata>
    <displayName>Amazon Machine Image Configuration</displayName>
    <descriptions>
      <desc>Amazon Machine Image Configuration</desc>
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
      <name>options.ebsBacked</name>
      <descriptions>
        <desc>Backed by EBS</desc>
      </descriptions>
      <type>bool</type>
      <default>false</default>
      <required>true</required>
    </field>
    <field>
      <name>options.amiHugeDiskMountpoint</name>
      <descriptions>
        <desc>Scratch-space mountpoint</desc>
      </descriptions>
      <help href="@Help_scratch_mountpoint@"/>
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
  </dataFields>
</descriptor>"""
