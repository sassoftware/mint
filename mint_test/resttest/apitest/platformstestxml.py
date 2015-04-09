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
  <imageTypeDefinitions href="http://localhost:8000/api/platforms/1/imageTypeDefinitions"/>%(platformVersions)s
</platform>
"""

platformXml = platformXmlTempl % dict(
    enabled="false",
    platformVersions="""
    %s""" % platformVersions)


platformPUTXml = platformXmlTempl % dict(
    enabled="true",
    platformVersions="")

platformGETXml = platformXmlTempl % dict(
    enabled="true",
    platformVersions="""
    %s""" % platformVersions)

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
      <displayName>VMware(R) ESX/VCD / Oracle(R) VirtualBox Virtual Appliance</displayName>
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
      <displayName>VMware(R) ESX/VCD / Oracle(R) VirtualBox Virtual Appliance</displayName>
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
