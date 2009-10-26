platformsXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/platforms/1">
    <platformId>1</platformId>
    <hostname>localhost@rpath:plat-1</hostname>
    <label>localhost@rpath:plat-1</label>
    <platformName>Crowbar Linux 1</platformName>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost@rpath:plat-1/api"/>
    <sources>
      <platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
        <platformSourceId>1</platformSourceId>
        <name>Platform 1 Source</name>
        <platformId>1</platformId>
        <shortname>plat1source</shortname>
        <sourceUrl>http://plat1source.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
      </platformSource>
    </sources>
    <platformMode>proxied</platformMode>
    <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  </platform>
  <platform id="http://localhost:8000/api/platforms/2">
    <platformId>2</platformId>
    <hostname>localhost@rpath:plat-2</hostname>
    <label>localhost@rpath:plat-2</label>
    <platformName>Crowbar Linux 2</platformName>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost@rpath:plat-2/api"/>
    <sources>
      <platformSource id="http://localhost:8000/api/platforms/2/sources/plat2source0">
        <platformSourceId>2</platformSourceId>
        <name>Platform 2 Source 0</name>
        <platformId>2</platformId>
        <shortname>plat2source0</shortname>
        <sourceUrl>https://plat2source0.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/2/sources/plat2source0/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/2/sources/plat2source0/descriptor"/>
      </platformSource>
      <platformSource id="http://localhost:8000/api/platforms/2/sources/plat2source1">
        <platformSourceId>3</platformSourceId>
        <name>Platform 2 Source 1</name>
        <platformId>2</platformId>
        <shortname>plat2source1</shortname>
        <sourceUrl>https://plat2source1.example.com</sourceUrl>
        <defaultSource>true</defaultSource>
        <orderIndex>0</orderIndex>
        <platformSourceStatus href="http://localhost:8000/api/platforms/2/sources/plat2source1/status"/>
        <configDescriptor href="http://localhost:8000/api/platforms/2/sources/plat2source1/descriptor"/>
      </platformSource>
    </sources>
    <platformMode>proxied</platformMode>
    <platformStatus href="http://localhost:8000/api/platforms/2/status"/>
  </platform>
</platforms>
"""

platformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform id="http://localhost:8000/api/platforms/1">
  <platformId>1</platformId>
  <hostname>localhost@rpath:plat-1</hostname>
  <label>localhost@rpath:plat-1</label>
  <platformName>Crowbar Linux 1</platformName>
  <enabled>true</enabled>
  <configurable>true</configurable>
  <repositoryUrl href="http://localhost:8000/repos/localhost@rpath:plat-1/api"/>
  <sources>
    <platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
      <platformSourceId>1</platformSourceId>
      <name>Platform 1 Source</name>
      <platformId>1</platformId>
      <shortname>plat1source</shortname>
      <sourceUrl>http://plat1source.example.com</sourceUrl>
      <defaultSource>true</defaultSource>
      <orderIndex>0</orderIndex>
      <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
      <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
    </platformSource>
  </sources>
  <platformMode>proxied</platformMode>
  <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
</platform>
"""

platformSourcesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<sources>
  <platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
    <platformSourceId>1</platformSourceId>
    <name>Platform 1 Source</name>
    <platformId>1</platformId>
    <shortname>plat1source</shortname>
    <sourceUrl>http://plat1source.example.com</sourceUrl>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
    <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
  </platformSource>
</sources>
"""

platformSourceXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
  <platformSourceId>1</platformSourceId>
  <name>Platform 1 Source</name>
  <platformId>1</platformId>
  <shortname>plat1source</shortname>
  <sourceUrl>http://plat1source.example.com</sourceUrl>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
  <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
</platformSource>
"""

platformSourceStatusXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>Username, password, and source url must be provided to check a source's status.</message>
</platformSourceStatus>
"""

platformSourceStatusDataXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Validated Successfully</message>
</platformSourceStatus>
"""

platformSourceStatusDataFailXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>false</valid>
  <message>Validation Failed</message>
</platformSourceStatus>
"""

platformSourceDescriptorXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Platform 1 Source</displayName>
    <descriptions>
      <desc>Configure Platform 1 Source</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>Username</desc>
      </descriptions>
      <prompt>
        <desc>Your RHN Username</desc>
      </prompt>
      <type>str</type>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Your RHN Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
  </dataFields>
</configDescriptor>
"""

platformSourcePUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
  <platformSourceId>1</platformSourceId>
  <name>Platform 1 Source</name>
  <platformId>1</platformId>
  <shortname>plat1source</shortname>
  <sourceUrl>http://plat1source.example.com</sourceUrl>
  <username>foousername</username>
  <password>foopassword</password>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
  <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
</platformSource>
"""

platformSourcePUTXml2 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSource id="http://localhost:8000/api/platforms/1/sources/plat1source">
  <platformSourceId>1</platformSourceId>
  <name>Platform 1 Source</name>
  <platformId>1</platformId>
  <shortname>plat1source</shortname>
  <sourceUrl>http://plat1source.example.com</sourceUrl>
  <username>foousername2</username>
  <password>foopassword2</password>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <platformSourceStatus href="http://localhost:8000/api/platforms/1/sources/plat1source/status"/>
  <configDescriptor href="http://localhost:8000/api/platforms/1/sources/plat1source/descriptor"/>
</platformSource>
"""
