platformsXml = """\
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
"""

#Prath
platformSourceXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<id="http://localhost:8000/api/v1/platforms/1/sources/plat1source">
  <platform href="1"/>
  <content_source href="1"/>
</platformSource>
"""

#Prath
platformSourceStatusXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message> </message>
  <content_source_status_id>1</content_source_status_id>
  <content_source_type href="1"/>
  <short_name>unique1</short_name>
</platformSourceStatus>
"""
#Prath
platformSourceStatusXml2 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message> </message>
  <content_source_status_id>2</content_source_status_id>
  <content_source_type href="2"/>
  <short_name>unique2</short_name>
</platformSourceStatus>
"""
#Prath
platformSourceStatusXml3 = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message> </message>
  <content_source_status_id>3</content_source_status_id>
  <content_source_type href="3"/>
  <short_name>unique3</short_name>
</platformSourceStatus>
"""

#untouched
contentSourceStatusXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>The following fields must be provided to check a source's status: User Name, Password.</message>
</contentSourceStatus>
"""

#untouched
contentSourceStatusDataXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Validated Successfully</message>
</contentSourceStatus>
"""
#untouched
contentSourceStatusDataFailXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<contentSourceStatus>
  <connected>true</connected>
  <valid>false</valid>
  <message>Validation Failed</message>
</contentSourceStatus>
"""

#Prath
contentSourceTypesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source_types>
  <content_source_type id="http://localhost:8000/api/v1/content_sources/1">
    <content_source_type>ContentSourceType</content_source_type>
  </content_source_type>
  <content_source_type id="http://localhost:8000/api/v1/content_sources/2">
    <content_source_type>ContentSourceType1</content_source_type>
  </content_source_type>
   <content_source_type id="http://localhost:8000/api/v1/content_sources/3">
    <content_source_type>ContentSourceType2</content_source_type>
  </content_source_type>
</content_source_types>
"""

contentSourceTypePUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source_type>ContentSourceType New</content_source_type>
"""

#untouched
contentSourcesXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<instances>
  <content_source id="http://localhost:8000/api/v1/contentSources/RHN/instances/plat2source0">
    <content_source_id>1</content_source_id>
    <name>Test</name>
    <short_name>Source</short_name>
    <default_source>True</default_source>
    <order_index>False</order_index>
    <content_source_type>ContentSourceType Object</content_source_type>
    <enabled>True</enabled>
    <content_source_status href="http://localhost:8000/api/v1/contentSources/RHN/instances/plat2source0/status"/>
  </content_source>
"""  

#Prath
contentSourcesByPlatformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_sources>
  <content_source id="http://localhost:8000/api/v1/content_sources/satellite/instances/plat1source">
    <content_source_id>1</content_source_id>
    <name>Test</name>
    <short_name>Source</short_name>
    <default_source>true</default_source>
    <order_index>0</order_index>
    <content_source_type>ContentSourceType Object</content_source_type>
    <enabled>true</enabled>
  </content_source>
  <content_source id="http://localhost:8000/api/v1/content_sources/satellite/instances/plat1source">
    <content_source_id>2</content_source_id>
    <name>content</name>
    <short_name>new source</short_name>
    <default_source>true</default_source>
    <order_index>0</order_index>
    <content_source_type>cst</content_source_type>
    <enabled>true</enabled>
  </content_source>
  <content_source id="http://localhost:8000/api/v1/contentSources/satellite/instances/plat1source">
    <content_source_id>3</content_source_id>
    <name>content1</name>
    <shortname>new source1</shortname>
    <default_source>true</default_source>
    <order_index>1</order_index>
    <content_source_type>cst2</content_source_type>
    <enabled>true</enabled>
  </content_source>
</content_sources>
"""

#untouched
contentSourceTypesByPlatformXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source_types>
  <content_source_type id="http://localhost:8000/api/v1/content_sources/RHN">
    <content_source_type>RHN</content_source_type>
  </content_source_type>
  <content_source_type id="http://localhost:8000/api/v1/content_sources/satellite">
    <content_source_type>satellite</content_source_type>
  </content_source_type>
</content_source_types>
"""

#Prath
contentSourcePUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source id="http://localhost:8000/api/v1/content_sources/RHN/instances/plat2source0">
  <content_source_id>2</content_source_id>
  <name>Platform 2 Source 0</name>
  <short_name>plat2source0</short_name>
  <default_source>true</default_source>
  <order_index>1</order_index>
  <enabled>true</enabled>
  <username>foousername</username>
  <password>foopassword</password>
</contentSource>
"""

#Prath
platformPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform>
    <label>PlatformTestPost</label>
    <platform_name>PlatformPost</platform_name>
    <mode>Platform</mode>
    <enabled>1</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
</platform>
"""

#Prath
platformPUTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform_id="http://localhost:8000/api/v1/platforms/1">
    <label>PlatformTest</label>
    <platform_name>Platform</platform_name>
    <mode>Platform</mode>
    <enabled>0</enabled>
    <configurable>true</configurable>
    <abstract>true</abstract>
    <project href="1"/>
</platform>
"""

#Prath
contentSourcePOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source>
  <name>PlatformTestPost</name>
  <short_name>PlatformTestPost</short_name>
  <default_source>true</default_source>
  <order_index>1</order_index>
  <enabled>true</enabled>
</content_source>
"""

#Prath
contentSourceTypePOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source_type>
  <content_source_type>ContentSourceTypePost</content_source_type>
  <required>true</required>
  <singleton>true</singleton>
</content_source_type>
"""

#Prath
platformLoadStatusPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformLoadStatus>
  <code>10</code>
  <message>PlatformLoadStatusPostTest</message>
  <is_final>true</is_final>
</platformLoadStatus>
"""

#Prath
platformLoadPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformLoad>
  <load_uri>platformLoadUri</load_uri>
  <job_id>10</job_id>
  <platform_id>10</platform_id>
  <platform_load_status href= "">
</platformLoad>
"""

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

#Prath
sourceStatusPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<sourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>sourceStatusPostTest</message>
  <content_source_type href=" ">
  <short_name>sourceStatusPostTest</short_name>
</sourceStatus>
"""

#only field tags changed
sourcePOSTRespXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source id="http://localhost:8000/api/v1/content_sources/RHN/instances/plat2source2">
  <content_source_id>4</content_source_id>
  <name>Platform 2 Source 2</name>
  <short_name>plat2source2</short_name>
  <default_source>false</default_source>
  <order_index>1</order_index>
  <content_source_type>RHN</content_source_type>
  <enabled>false</enabled>
  <content_source_status href="http://localhost:8000/api/v1/content_sources/RHN/instances/plat2source2/status"/>
</content_source>
"""

#unchanged
sourcePOST2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source>
  <name>Platform 2 Source 2</name>
  <short_name>plat2source2</short_name>
  <source_url>https://plat2source2.example.com</source_url>
  <default_source>false</default_source>
  <order_index>1</order_index>
  <content_source_type>satellite</content_source_type>
</content_source>
"""

#unchanged
sourcePOSTResp2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source id="http://localhost:8000/api/v1/content_sources/satellite/instances/plat2source2">
  <content_source_id>4</content_source_id>
  <name>Platform 2 Source 2</name>
  <short_name>plat2source2</short_name>
  <default_source>false</default_source>
  <order_index>1</order_index>
  <content_source_type>satellite</content_source_type>
  <enabled>false</enabled>
  <source_url>https://plat2source2.example.com</source_url>
</content_source>
"""

#unchanged
statusTestPOSTXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<content_source>
  <name>Platform 2 Source 2</name>
  <shortname>plat2source2</shortname>
  <username>foousername</username>
  <password>foopassword</password>
  <sourceUrl>https://plat2source2.example.com</sourceUrl>
  <defaultSource>false</defaultSource>
  <orderIndex>1</orderIndex>
  <contentSourceType>RHN</contentSourceType>
</content_source>
"""

#fields changed
statusTestPOSTRespXml = """\
<?xml version='1.0' encoding='UTF-8'?>
<SourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Validated Successfully</message>
</SourceStatus>
"""

#fields changed
platformStatusXml = """\
<SourceStatus>
  <connected>false</connected>
  <valid>false</valid>
  <message>Platform must be enabled to check its status.</message>
</SourceStatus>
"""

#only fields changed
platformStatus2Xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<SourceStatus>
  <connected>true</connected>
  <valid>true</valid>
  <message>Available.</message>
</SourceStatus>
"""

#unchanged
platformImageDefXml = """\
<imageTypeDefinitions>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204/architectures/x86">
      <name>x86</name>
      <displayName>x86</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204/flavorsets/xen">
      <name>xen</name>
      <displayName>Xen DomU</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/71a60de01b7e8675254175584fdb9db2">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/71a60de01b7e8675254175584fdb9db2/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/71a60de01b7e8675254175584fdb9db2/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/71a60de01b7e8675254175584fdb9db2/flavorsets/xen">
      <name>xen</name>
      <displayName>Xen DomU</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/072f6883c0290204e26de6f4e66c5c54">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/072f6883c0290204e26de6f4e66c5c54/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="true"/>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/072f6883c0290204e26de6f4e66c5c54/architectures/x86">
      <name>x86</name>
      <displayName>x86</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/072f6883c0290204e26de6f4e66c5c54/flavorsets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://localhost:8000/api/platforms/1/imageTypeDefinitions/e0b2438053d04a63f74ef5e7794e42a1">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <container id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/e0b2438053d04a63f74ef5e7794e42a1/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="true" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="true"/>
    </container>
    <architecture id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/e0b2438053d04a63f74ef5e7794e42a1/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://localhost:8000/api/platforms/1/imagesTypeDefinitions/e0b2438053d04a63f74ef5e7794e42a1/flavorsets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
</imageTypeDefinitions>
"""
