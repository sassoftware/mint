platformsXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platforms>
  <platform id="http://localhost:8000/api/platforms/1">
    <platformId>1</platformId>
    <repositoryHostname>localhost</repositoryHostname>
    <label>localhost@rpath:plat-1</label>
    <platformName>Crowbar Linux 1</platformName>
    <platformUsageTerms>Terms of Use 1</platformUsageTerms>
    <mode>manual</mode>
    <enabled>false</enabled>
    <configurable>true</configurable>
    <abstract>false</abstract>
    <hidden>false</hidden>
    <mirrorPermission>true</mirrorPermission>
    <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
    <contentSources href="http://localhost:8000/api/platforms/1/contentSources"/>
    <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
    <contentSourceTypes href="http://localhost:8000/api/platforms/1/contentSourceTypes"/>
    <load href="http://localhost:8000/api/platforms/1/load/"/>
    <imageTypeDefinitions href="http://localhost:8000/api/platforms/1/imageTypeDefinitions"/>
    <platformVersions href="http://localhost:8000/api/platforms/1/platformVersions/"/>
  </platform>
  <platform id="http://localhost:8000/api/platforms/2">
    <platformId>2</platformId>
    <repositoryHostname>localhost</repositoryHostname>
    <label>localhost@rpath:plat-2</label>
    <platformName>Crowbar Linux 2</platformName>
    <platformUsageTerms>Terms of Use 2</platformUsageTerms>
    <mode>manual</mode>
    <enabled>false</enabled>
    <configurable>true</configurable>
    <abstract>false</abstract>
    <hidden>false</hidden>
    <mirrorPermission>true</mirrorPermission>
    <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
    <contentSources href="http://localhost:8000/api/platforms/2/contentSources"/>
    <platformStatus href="http://localhost:8000/api/platforms/2/status"/>
    <contentSourceTypes href="http://localhost:8000/api/platforms/2/contentSourceTypes"/>
    <load href="http://localhost:8000/api/platforms/2/load/"/>
    <imageTypeDefinitions href="http://localhost:8000/api/platforms/2/imageTypeDefinitions"/>
    <platformVersions href="http://localhost:8000/api/platforms/2/platformVersions/"/>
  </platform>
</platforms>
"""

platformVersions = """<platformVersions href="http://localhost:8000/api/platforms/1/platformVersions/"/>"""

platformXmlTempl = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform id="http://localhost:8000/api/platforms/1">
  <platformId>1</platformId>
  <repositoryHostname>localhost</repositoryHostname>
  <label>localhost@rpath:plat-1</label>
  <platformName>Crowbar Linux 1</platformName>
  <platformUsageTerms>Terms of Use 1</platformUsageTerms>
  <mode>manual</mode>
  <enabled>%(enabled)s</enabled>
  <configurable>true</configurable>
  <abstract>false</abstract>
  <hidden>false</hidden>
  <mirrorPermission>true</mirrorPermission>
  <repositoryUrl href="http://localhost:8000/repos/localhost./api"/>
  <upstreamUrl/>
  <contentSources href="http://localhost:8000/api/platforms/1/contentSources"/>
  <platformStatus href="http://localhost:8000/api/platforms/1/status"/>
  <contentSourceTypes href="http://localhost:8000/api/platforms/1/contentSourceTypes"/>
  <load href="http://localhost:8000/api/platforms/1/load/"/>
  <imageTypeDefinitions href="http://localhost:8000/api/platforms/1/imageTypeDefinitions"/>%(platformVersions)s
</platform>
"""

platformXml = platformXmlTempl % dict(
    enabled="false",
    platformVersions="""
    %s""" % platformVersions)

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
  <message>Available.</message>
</platformSourceStatus>
"""

platformSourceStatusXml2 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message> Repository not responding: https://localhost/conary/.</message>
</platformSourceStatus>
"""

platformSourceStatusXml3 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>false</valid>
  <message> Error connecting to repository https://localhost/conary/: .</message>
</platformSourceStatus>
"""

platformSourceStatusXml4 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>false</valid>
  <message> Repository is empty, please manually load the preload for this platform available from http://docs.rpath.com/platforms/platform_repositories.html.</message>
</platformSourceStatus>
"""

platformSourceStatusXml5 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message> Error connecting to repository https://localhost/conary/: .</message>
</platformSourceStatus>
"""

contentSourceStatusXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>The following fields must be provided to check a source's status: User Name, Password.</message>
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
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
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
        <desc>User Name</desc>
      </descriptions>
      <prompt>
        <desc>User Name</desc>
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
        <desc>Source URL</desc>
      </descriptions>
      <prompt>
        <desc>Source URL</desc>
      </prompt>
      <type>str</type>
      <password>false</password>
      <constraints>
        <descriptions>
          <desc>URL must begin with ftp://, http://, or https://</desc>
        </descriptions>
        <regexp>^(http|https|ftp):\/\/.*</regexp>
      </constraints>
    </field>
  </dataFields>
</configDescriptor>
"""

contentSourceTypesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceTypes>
  <contentSourceType id="http://localhost:8000/api/contentSources/RHN">
    <contentSourceType>RHN</contentSourceType>
    <required>true</required>
    <singleton>true</singleton>
    <instances href="http://localhost:8000/api/contentSources/RHN/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/RHN/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/RHN/statusTest"/>
  </contentSourceType>
  <contentSourceType id="http://localhost:8000/api/contentSources/satellite">
    <contentSourceType>satellite</contentSourceType>
    <required>false</required>
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
  <required>true</required>
  <singleton>true</singleton>
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
    <orderIndex>1</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <enabled>false</enabled>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source1">
    <contentSourceId>3</contentSourceId>
    <name>Platform 2 Source 1</name>
    <shortname>plat2source1</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>2</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <enabled>false</enabled>
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
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <enabled>false</enabled>
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
    <enabled>false</enabled>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/satellite/instances/plat1source/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/satellite/instances/plat1source/errors/"/>
    <sourceUrl>http://plat1source.example.com</sourceUrl>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source0">
    <contentSourceId>2</contentSourceId>
    <name>Platform 2 Source 0</name>
    <shortname>plat2source0</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>1</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <enabled>false</enabled>
    <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
    <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  </contentSource>
  <contentSource id="http://localhost:8000/api/contentSources/RHN/instances/plat2source1">
    <contentSourceId>3</contentSourceId>
    <name>Platform 2 Source 1</name>
    <shortname>plat2source1</shortname>
    <defaultSource>true</defaultSource>
    <orderIndex>2</orderIndex>
    <contentSourceType>RHN</contentSourceType>
    <enabled>false</enabled>
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
    <required>true</required>
    <singleton>true</singleton>
    <instances href="http://localhost:8000/api/contentSources/RHN/instances/"/>
    <configDescriptor href="http://localhost:8000/api/contentSources/RHN/descriptor"/>
    <statusTest href="http://localhost:8000/api/contentSources/RHN/statusTest"/>
  </contentSourceType>
  <contentSourceType id="http://localhost:8000/api/contentSources/satellite">
    <contentSourceType>satellite</contentSourceType>
    <required>false</required>
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
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <enabled>true</enabled>
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
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <enabled>true</enabled>
  <contentSourceStatus href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/status"/>
  <resourceErrors href="http://localhost:8000/api/contentSources/RHN/instances/plat2source0/errors/"/>
  <username>foousername2</username>
  <password>foopassword2</password>
</contentSource>
"""

platformPUTXml = platformXmlTempl % dict(
    enabled="true",
    platformVersions="")

platformGETXml = platformXmlTempl % dict(
    enabled="true",
    platformVersions="""
    %s""" % platformVersions)

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
  <contentSourceId>4</contentSourceId>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
  <enabled>false</enabled>
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
  <contentSourceId>4</contentSourceId>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>satellite</contentSourceType>
  <enabled>false</enabled>
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

platformStatusXml = """\
<platformSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>Platform must be enabled to check its status.</message>
</platformSourceStatus>
"""

platformStatus2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Available.</message>
</platformSourceStatus>
"""

platformImageDefXml = """\
<imageTypeDefinitions>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/3580ab1481bf29998e62cb8111a6833a">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/3580ab1481bf29998e62cb8111a6833a/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/3580ab1481bf29998e62cb8111a6833a/architectures/x86">
      <name>x86</name>
      <displayName>x86</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/3580ab1481bf29998e62cb8111a6833a/flavorsets/xen">
      <name>xen</name>
      <displayName>Xen DomU</displayName>
    </flavorSet>
    <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/76374bd15c72d81d733ddc309d4a5b86">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/76374bd15c72d81d733ddc309d4a5b86/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/76374bd15c72d81d733ddc309d4a5b86/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/76374bd15c72d81d733ddc309d4a5b86/flavorsets/xen">
      <name>xen</name>
      <displayName>Xen DomU</displayName>
    </flavorSet>
    <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/724a58650a441a12a0103e8961c4f4fd">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/724a58650a441a12a0103e8961c4f4fd/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/724a58650a441a12a0103e8961c4f4fd/architectures/x86">
      <name>x86</name>
      <displayName>x86</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/724a58650a441a12a0103e8961c4f4fd/flavorsets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="true"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/b2cbbc10ed9cc9f756cab7f7d8685708">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/b2cbbc10ed9cc9f756cab7f7d8685708/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/b2cbbc10ed9cc9f756cab7f7d8685708/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/b2cbbc10ed9cc9f756cab7f7d8685708/flavorsets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="true"/>
  </imageTypeDefinition>
</imageTypeDefinitions>
"""
