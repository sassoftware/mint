platformsXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/v1/platforms/5">
    <platform_id>5</platform_id>
    <platform_name>Platform5</platform_name>
    <label>Platform5label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="1"/>
  </platform>
  <platform id="http://localhost:8000/api/v1/platforms/6">
    <platform_id>6</platform_id>
    <platform_name>Platform6</platform_name>
    <label>Platform6label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="2"/>
  </platform>
  <platform id="http://localhost:8000/api/v1/platforms/7">
    <platform_id>7</platform_id>
    <platform_name>Platform7</platform_name>
    <label>Platform7label</label>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <project href="3"/>
  </platform>
</platforms>
""".strip()

platformPOSTXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platform>
    <platform_name>Platform5</platform_name>
    <label>PlatformMyPlatformLabel2</label>
    <mode>manual</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <is_from_disk>true</is_from_disk>
    <projects id="http://localhost:8000/api/v1/projects/morbeef" />
</platform>
""".strip()

#Prath
platformPUTXml = \
"""
<?xml version='1.0' encoding='UTF-8'?>
<platform>
    <label>PlatformChanged</label>
    <platform_name>Platform Name Changed</platform_name>
    <mode>auto</mode>
    <enabled>0</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
</platform>
""".strip()


#Prath
platformVersionPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformVersion>
  <name>PlatformVersionPostTest</name>
  <version>Post</version>
  <revision>Post</revision>
  <label>PlatformVersionPostTest</label>
  <ordering>PlatformVersionPostTest</ordering>
</platformVersion>
"""


deferred_image_descriptor_xml = """
<descriptor xmlns="http://www.rpath.com/permanent/descriptor-1.1.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd" version="1.1">
  <dataFields>
    <field>
      <descriptions>
        <desc>Image Name</desc>
      </descriptions>
      <multiple>false</multiple>
      <name>displayName</name>
      <required>true</required>
      <type>str</type>
    </field>
    <field>
      <descriptions/>
      <type>enumeratedType</type>
      <enumeratedType>
        <describedValue>
          <descriptions>
            <desc>alpha</desc>
          </descriptions>
        <key>dummy-trove=/example.rpath.com@dummy:label/1.0-1-1</key>
        </describedValue>
        <describedValue>
          <descriptions>
            <desc>beta</desc>
          </descriptions>
          <key>dummy-trove=/example.rpath.com@dummy:label/1.0-1-1</key>
        </describedValue>
      </enumeratedType>
      <multiple>false</multiple>
      <name>options.baseImageTrove</name>
      <readonly>false</readonly>
      <required>true</required>
    </field>
  </dataFields>
  <metadata>
    <descriptions>
      <desc>Layered Image Configuration</desc>
    </descriptions>
    <displayName>Layered Image Configuration</displayName>
    <rootElement>descriptor_data</rootElement>
  </metadata>
</descriptor>
"""

deferred_image_descriptor_no_base_images_xml = """
<descriptor xmlns="http://www.rpath.com/permanent/descriptor-1.1.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.1.xsd descriptor-1.1.xsd" version="1.1">
  <dataFields>
    <field>
      <descriptions>
        <desc>Image Name</desc>
      </descriptions>
      <multiple>false</multiple>
      <name>displayName</name>
      <required>true</required>
      <type>str</type>
    </field>
    <field>
      <descriptions/>
      <type>enumeratedType</type>
      <enumeratedType>
        <describedValue>
          <descriptions>
            <desc>No base images available</desc>
          </descriptions>
        <key>nobaseimagesavailable</key>
        </describedValue>
      </enumeratedType>
      <default>nobaseimagesavailable</default>
      <multiple>false</multiple>
      <name>options.baseImageTrove</name>
      <required>true</required>
      <readonly>true</readonly>
    </field>
  </dataFields>
  <metadata>
    <descriptions>
      <desc>Layered Image Configuration</desc>
    </descriptions>
    <displayName>Layered Image Configuration</displayName>
    <rootElement>descriptor_data</rootElement>
  </metadata>
</descriptor>
"""

