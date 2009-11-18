platformsXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/platforms/1">
    <platformId>1</platformId>
    <repositoryHostname>localhost</repositoryHostname>
    <label>localhost@rpath:plat-1</label>
    <platformName>Crowbar Linux 1</platformName>
    <mode>manual</mode>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
    <contentSources href="http://localhost:8000/api/platforms/1/contentSources"/>
    <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
    <contentSourceTypes href="http://localhost:8000/api/platforms/1/contentSourceTypes"/>
    <load href="http://localhost:8000/api/platforms/1/load/"/>
  </platform>
  <platform id="http://localhost:8000/api/platforms/2">
    <platformId>2</platformId>
    <repositoryHostname>localhost</repositoryHostname>
    <label>localhost@rpath:plat-2</label>
    <platformName>Crowbar Linux 2</platformName>
    <mode>manual</mode>
    <enabled>true</enabled>
    <configurable>true</configurable>
    <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
    <contentSources href="http://localhost:8000/api/platforms/2/contentSources"/>
    <platformStatus href="http://localhost:8000/api/platforms/2/status"/>
    <contentSourceTypes href="http://localhost:8000/api/platforms/2/contentSourceTypes"/>
    <load href="http://localhost:8000/api/platforms/2/load/"/>
  </platform>
</platforms>
"""

platformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform id="http://localhost:8000/api/platforms/1">
  <platformId>1</platformId>
  <repositoryHostname>localhost</repositoryHostname>
  <label>localhost@rpath:plat-1</label>
  <platformName>Crowbar Linux 1</platformName>
  <mode>manual</mode>
  <enabled>true</enabled>
  <configurable>true</configurable>
  <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
  <contentSources href="http://localhost:8000/api/platforms/1/contentSources"/>
  <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  <contentSourceTypes href="http://localhost:8000/api/platforms/1/contentSourceTypes"/>
  <load href="http://localhost:8000/api/platforms/1/load/"/>
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
  <connected>true</connected>
  <valid>true</valid>
  <message>Crowbar Linux 1 is online.</message>
</platformSourceStatus>
"""

contentSourceStatusXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>The following fields must be provided to check a source's status: ['username', 'password'].</message>
</contentSourceStatus>
"""

contentSourceStatusDataXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Validated Successfully</message>
</contentSourceStatus>
"""

contentSourceStatusDataFailXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>true</connected>
  <valid>false</valid>
  <message>Validation Failed</message>
</contentSourceStatus>
"""

sourceDescriptorXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Red Hat Network</displayName>
    <descriptions>
      <desc>Red Hat Network Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>Username</desc>
      </descriptions>
      <prompt>
        <desc>Username</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
  </dataFields>
</configDescriptor>
"""

sourceDescriptor2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<configDescriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd">
  <metadata>
    <displayName>Red Hat Satellite</displayName>
    <descriptions>
      <desc>Red Hat Satellite Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>name</name>
      <required>true</required>
      <descriptions>
        <desc>Name</desc>
      </descriptions>
      <prompt>
        <desc>Name</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>username</name>
      <required>true</required>
      <descriptions>
        <desc>Username</desc>
      </descriptions>
      <prompt>
        <desc>Username</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
    <field>
      <name>password</name>
      <required>true</required>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <prompt>
        <desc>Password</desc>
      </prompt>
      <type>str</type>
      <password>true</password>
    </field>
    <field>
      <name>sourceUrl</name>
      <required>true</required>
      <descriptions>
        <desc>Source Url</desc>
      </descriptions>
      <prompt>
        <desc>Source Url</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
    </field>
  </dataFields>
</configDescriptor>
"""

contentSourceTypesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceTypes>
  <contentSourceType id="http://localhost:8000/api/contentSources/RHN">
    <contentSourceType>RHN</contentSourceType>
    <instances href="http://localhost:8000/api/contentSources/RHN/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/RHN/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/RHN/statusTest"/>
  </contentSourceType>
  <contentSourceType id="http://localhost:8000/api/contentSources/satellite">
    <contentSourceType>satellite</contentSourceType>
    <instances href="http://localhost:8000/api/contentSources/satellite/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/satellite/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/satellite/statusTest"/>
  </contentSourceType>
</contentSourceTypes>
"""

contentSourceTypeXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceType id="http://localhost:8000/api/contentSources/RHN">
  <contentSourceType>RHN</contentSourceType>
  <instances href="http://localhost:8000/api/contentSources/RHN/instances/"/>
  <configDescriptor href="http://localhost:8000/api/contentSources/RHN/descriptor"/>
  <statusTest href="http://localhost:8000/api/contentSources/RHN/statusTest"/>
</contentSourceType>
"""

contentSourcesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<instances>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
    <contentSourceId>2</contentSourceId>
    <name>Platform 2 Source 0</name>
    <shortname>plat2source0</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source1">
    <contentSourceId>3</contentSourceId>
    <name>Platform 2 Source 1</name>
    <shortname>plat2source1</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source1/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source1/errors/"/>
  </contentSource>
</instances>
"""

contentSourceXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
  <contentSourceId>2</contentSourceId>
  <name>Platform 2 Source 0</name>
  <shortname>plat2source0</shortname>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
</contentSource>
"""

contentSourcesByPlatformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSources>
  <contentSource id="http://localhost:8000/api/contentSources/satellite/instances/plat1source">
    <contentSourceId>1</contentSourceId>
    <name>Platform 1 Source</name>
    <shortname>plat1source</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <contentSourceType>satellite</contentSourceType>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/satellite/instances/plat1source/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/satellite/instances/plat1source/errors/"/>
    <sourceUrl>http://plat1source.example.com</sourceUrl>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
    <contentSourceId>2</contentSourceId>
    <name>Platform 2 Source 0</name>
    <shortname>plat2source0</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source1">
    <contentSourceId>3</contentSourceId>
    <name>Platform 2 Source 1</name>
    <shortname>plat2source1</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>0</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source1/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source1/errors/"/>
  </contentSource>
</contentSources>
"""

contentSourceTypesByPlatformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceTypes>
  <contentSourceType id="http://localhost:8000/api/contentSources/RHN">
    <contentSourceType>RHN</contentSourceType>
    <instances href="http://localhost:8000/api/contentSources/RHN/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/RHN/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/RHN/statusTest"/>
  </contentSourceType>
  <contentSourceType id="http://localhost:8000/api/contentSources/satellite">
    <contentSourceType>satellite</contentSourceType>
    <instances href="http://localhost:8000/api/contentSources/satellite/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/satellite/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/satellite/statusTest"/>
  </contentSourceType>
</contentSourceTypes>
"""

contentSourcePUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
  <contentSourceId>2</contentSourceId>
  <name>Platform 2 Source 0</name>
  <shortname>plat2source0</shortname>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  <username>foousername</username>
  <password>foopassword</password>
</contentSource>
"""

contentSourcePUTXml2 = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
  <contentSourceId>2</contentSourceId>
  <name>Platform 2 Source 0</name>
  <shortname>plat2source0</shortname>
  <defaultSource>true</defaultSource>
  <orderIndex>0</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  <username>foousername2</username>
  <password>foopassword2</password>
</contentSource>
"""

platformPUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform id="http://localhost:8000/api/platforms/1">
  <platformId>1</platformId>
  <repositoryHostname>localhost</repositoryHostname>
  <label>localhost@rpath:plat-1</label>
  <platformName>Crowbar Linux 1</platformName>
  <mode>manual</mode>
  <enabled>true</enabled>
  <configurable>true</configurable>
  <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
  <contentSources href="http://localhost:8000/api/platforms/1/contentSources"/>
  <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  <contentSourceTypes href="http://localhost:8000/api/platforms/1/contentSourceTypes"/>
  <load href="http://localhost:8000/api/platforms/1/load/"/>
</platform>
"""

sourcePOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <sourceUrl>https://plat2source2.example.com</sourceUrl>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
</contentSource>
"""

sourcePOSTRespXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source2">
  <contentSourceId>1</contentSourceId>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source2/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source2/errors/"/>
</contentSource>
"""

sourcePOST2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <sourceUrl>https://plat2source2.example.com</sourceUrl>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>satellite</contentSourceType>
</contentSource>
"""

sourcePOSTResp2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource id="http://localhost:8000/api/contentSources/satellite/instances/plat2source2">
  <contentSourceId>1</contentSourceId>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>satellite</contentSourceType>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/satellite/instances/plat2source2/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/satellite/instances/plat2source2/errors/"/>
  <sourceUrl>https://plat2source2.example.com</sourceUrl>
</contentSource>
"""

statusTestPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSource>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <username>foousername</username>
  <password>foopassword</password>
  <sourceUrl>https://plat2source2.example.com</sourceUrl>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
</contentSource>
"""

statusTestPOSTRespXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Validated Successfully</message>
</contentSourceStatus>
"""
