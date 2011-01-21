#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import re
import StringIO
import time

from conary.lib import util

import restbase
from restlib import client as restClient
from testutils import mock
ResponseError = restClient.ResponseError

class ProductVersionTest(restbase.BaseRestTest):
    buildDefs = [
        ('Citrix XenServer 32-bit', 'xen', 'x86', 'xenOvaImage'),
        ('Citrix XenServer 64-bit', 'xen', 'x86_64', 'xenOvaImage'),
        ('VMware ESX 32-bit', 'vmware', 'x86', 'vmwareEsxImage'),
        ('VMware ESX 64-bit', 'vmware', 'x86_64', 'vmwareEsxImage'),
    ]

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testGetProductVersion(self):
        uriTemplate = 'products/%s/versions/%s/'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        client = self.getRestClient()
        req, response = client.call('GET', uri)
        resp = client.convert('xml', req, response)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<productVersion id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">
  <versionId>1</versionId>
  <hostname>testproject</hostname>
  <name>1.0</name>
  <productUrl href="http://%(server)s:%(port)s/api/products/testproject"/>
  <nameSpace>yournamespace</nameSpace>
  <description>Version description</description>
  <timeCreated></timeCreated>
  <platform href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/platform"/>
  <stages href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/"/>
  <definition href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/definition"/>
  <imageTypeDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions"/>
  <imageDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions"/>
  <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/images"/>
  <sourceGroup>group-testproject-appliance</sourceGroup>
</productVersion>
"""
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server))

    def testGetProductDefinition(self):
        uriTemplate = 'products/%s/versions/%s/definition'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri)
        sio = StringIO.StringIO()
        self.productDefinition.serialize(sio)
        self.failUnlessEqual(response.get(), sio.getvalue())

    def testGetStageImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/stages/%s/imageDefinitions'
        uri = uriTemplate % (self.productShortName, self.productVersion,
        'Development')
        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri, convert = True)

        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<imageDefinitions>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/71a60de01b7e8675254175584fdb9db2">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/072f6883c0290204e26de6f4e66c5c54">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/e0b2438053d04a63f74ef5e7794e42a1">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageDefinition>
</imageDefinitions>
"""
        self.failUnlessEqual(response,
            exp % dict(server = client.server, port = client.port))

    def testGetImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageDefinitions'
        uri = uriTemplate % (self.productShortName, self.productVersion)

        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri, convert=True)

        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<imageDefinitions>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/71a60de01b7e8675254175584fdb9db2">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/072f6883c0290204e26de6f4e66c5c54">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/e0b2438053d04a63f74ef5e7794e42a1">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageDefinition>
</imageDefinitions>
"""
        self.assertXMLEquals(response,
            exp % dict(server = client.server, port = client.port))

    def testGetImageTypeDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageTypeDefinitions'
        uri = uriTemplate % (self.productShortName, self.productVersion)

        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri, convert = True)

        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<imageTypeDefinitions>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/f46462c1c645ac92a50b6b651856be2c">
    <name>ami_large</name>
    <displayName>EC2 AMI Large/Huge</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/amiImage">
      <name>amiImage</name>
      <displayName>Amazon Machine Image (EC2)</displayName>
      <options amiHugeDiskMountpoint="False" autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="1024"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/ami">
      <name>ami</name>
      <displayName>AMI</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/9398d36b47c37fe00afbc0fcde8cb4ee">
    <name>ec2_small</name>
    <displayName>EC2 AMI Small</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/amiImage">
      <name>amiImage</name>
      <displayName>Amazon Machine Image (EC2)</displayName>
      <options amiHugeDiskMountpoint="False" autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="1024"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/ami">
      <name>ami</name>
      <displayName>AMI</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/2ebe0a8a2711b1fd9c45a4a54783d958">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/9d70e5f827bb4a69796af5d495a095b8">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/installableIsoImage">
      <name>installableIsoImage</name>
      <displayName>Legacy Installable CD/DVD</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/9e479ab19bb4527d14ee09869da556e4">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/b929b71a97c06306608c7249d41e8cd5">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/e72f6773f09b5d90b5f6070d00f53348">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/installableIsoImage">
      <name>installableIsoImage</name>
      <displayName>Legacy Installable CD/DVD</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/24597af6ccdf86fbfdc1b011f61e8204">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/7f1bcd23b75b9abe35a654ee672e8d83">
    <name>hyper_v</name>
    <displayName>MS Hyper-V</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vhdImage">
      <name>vhdImage</name>
      <displayName>VHD for Microsoft(R) Hyper-V(R)</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
      <name>generic</name>
      <displayName>Generic</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/477efa42a4fff42afedb52569a536acb">
    <name>hyper_v</name>
    <displayName>MS Hyper-V</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vhdImage">
      <name>vhdImage</name>
      <displayName>VHD for Microsoft(R) Hyper-V(R)</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
      <name>generic</name>
      <displayName>Generic</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/46e02da26faa3fc6f28dbba2c7e61f97">
    <name>raw_fs</name>
    <displayName>Raw Filesystem</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawFsImage">
      <name>rawFsImage</name>
      <displayName>Eucalyptus/Mountable Filesystem</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/e8d302c71efd138147801ccbe61abc4c">
    <name>raw_fs</name>
    <displayName>Raw Filesystem</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawFsImage">
      <name>rawFsImage</name>
      <displayName>Eucalyptus/Mountable Filesystem</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/bcee8d0d819ad99f874ab1fd74b9d8ec">
    <name>raw_hd</name>
    <displayName>Raw Hard Disk</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawHdImage">
      <name>rawHdImage</name>
      <displayName>KVM/Parallels/QEMU/Raw Hard Disk</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/3aae18937882de71b6cd9229fa2f0f25">
    <name>raw_hd</name>
    <displayName>Raw Hard Disk</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawHdImage">
      <name>rawHdImage</name>
      <displayName>KVM/Parallels/QEMU/Raw Hard Disk</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/a5c322b10d9e0cd14fea15d2acf5fff1">
    <name>tar</name>
    <displayName>Tar Image</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/tarballImage">
      <name>tarballImage</name>
      <displayName>TAR File</displayName>
      <options autoResolve="false" baseFileName="" installLabelPath="" swapSize="0"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/2bd4a4bfbba51d46146f23fa9627d459">
    <name>tar</name>
    <displayName>Tar Image</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/tarballImage">
      <name>tarballImage</name>
      <displayName>TAR File</displayName>
      <options autoResolve="false" baseFileName="" installLabelPath="" swapSize="0"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/35a69475aa5228be005fac59249b2abc">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareImage">
      <name>vmwareImage</name>
      <displayName>VMware(R) Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" diskAdapter="lsilogic" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/072f6883c0290204e26de6f4e66c5c54">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/a14e4f7d8161f23e8c5c7e4ba1988762">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareImage">
      <name>vmwareImage</name>
      <displayName>VMware(R) Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" diskAdapter="lsilogic" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="false"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/e0b2438053d04a63f74ef5e7794e42a1">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX(R) Server Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/201264007ec0d331b626ca074a841fa7">
    <name>virtual_iron</name>
    <displayName>Virtual Iron</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/ccb695f3ea5c111856a37907ca1de4fa">
    <name>virtual_iron</name>
    <displayName>Virtual Iron</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/9a1ffeb422bd48550ac2f3ccef4b6204">
    <name>xen_ova</name>
    <displayName>Xen OVA</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/71a60de01b7e8675254175584fdb9db2">
    <name>xen_ova</name>
    <displayName>Xen OVA</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageTypeDefinition>
</imageTypeDefinitions>
"""
        self.assertXMLEquals(response,
            exp % dict(server = client.server, port = client.port))

    def testGetProductVersionStages(self):
        uriTemplate = 'products/%s/versions/%s/stages'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri, convert = True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<stages>
  <stage id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development">
    <hostname>testproject</hostname>
    <version>1.0</version>
    <name>Development</name>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0-devel</label>
    <isPromotable>true</isPromotable>
    <groups href="http://%(server)s:%(port)s/api/products/testproject/repos/search?type=group&amp;label=testproject.rpath.local2@yournamespace:testproject-1.0-devel"/>
    <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development/images"/>
  </stage>
  <stage id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA">
    <hostname>testproject</hostname>
    <version>1.0</version>
    <name>QA</name>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0-qa</label>
    <isPromotable>true</isPromotable>
    <groups href="http://%(server)s:%(port)s/api/products/testproject/repos/search?type=group&amp;label=testproject.rpath.local2@yournamespace:testproject-1.0-qa"/>
    <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA/images"/>
  </stage>
  <stage id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release">
    <hostname>testproject</hostname>
    <version>1.0</version>
    <name>Release</name>
    <label>testproject.rpath.local2@yournamespace:testproject-1.0</label>
    <isPromotable>false</isPromotable>
    <groups href="http://%(server)s:%(port)s/api/products/testproject/repos/search?type=group&amp;label=testproject.rpath.local2@yournamespace:testproject-1.0"/>
    <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release/images"/>
  </stage>
</stages>
"""
        self.failUnlessEqual(response,
            exp % dict(server = client.server, port = client.port))

    def testPutProductVersionStages(self):
        uriTemplate = 'products/%s/versions/%s/stages/QA'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('PUT', uri, body=promoteGroup % dict(
                name = self.productShortName,
                ),
                convert=False)
        exp = """\
"""
        #self.failUnlessEqual(response,
        #    exp % dict(server = client.server, port = client.port))

        uriTemplate = 'products/%s/versions/%s/stages/QA/jobs/%s'
        uri = uriTemplate % (self.productShortName, self.productVersion
                             ,response.jobId)
        req, response = client.call('GET', uri, convert=True)

    def testSetProductVersionPlatform(self):
        self.setupPlatforms()
        from mint.rest.db import platformmgr
        mock.mock(platformmgr.Platforms, '_checkMirrorPermissions',
                        True)
        self.mock(restbase.proddef.PlatformDefinition, 'snapshotVersions',
            lambda slf, conaryClient, platformVersion = None: None)
        uriTemplate = 'products/%s/versions/%s/platform'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        client = self.getRestClient(username='foouser', admin=True)

        label = 'localhost@rpath:plat-2'
        data = """\
<platform>
  <label>%s</label>
</platform>
""" % label
        req, response = client.call('PUT', uri, data, convert = True)
        expected = """\
<platform id="http://localhost:8000/api/products/testproject/versions/1.0/platform">
  <platformId>2</platformId>
  <platformTroveName>platform-definition</platformTroveName>
  <label>localhost@rpath:plat-2</label>
  <platformVersion>4.2-1</platformVersion>
  <productVersion>1.0</productVersion>
  <platformName>Crowbar Linux 2</platformName>
  <enabled>true</enabled>
  <contentSources href="http://localhost:8000/api/platforms/2/contentSources"/>
  <platformStatus href="http://localhost:8000/api/platforms/2/status"/>
  <contentSourceTypes href="http://localhost:8000/api/platforms/2/contentSourceTypes"/>
  <load href="http://localhost:8000/api/platforms/2/load/"/>
  <imageTypeDefinitions href="http://localhost:8000/api/platforms/2/imageTypeDefinitions"/>
</platform>
"""
        self.assertXMLEquals(response, expected)

        # Make sure a GET fetches the same thing
        req, response = client.call('GET', uri, convert = True)
        self.assertXMLEquals(response, expected)

    def testGetProductVersionPlatform(self):
        uriTemplate = 'products/%s/versions/%s/platform'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        self.createUser('foouser')
        client = self.getRestClient(username='foouser')
        req, response = client.call('GET', uri, convert = True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<platform id="http://localhost:8000/api/products/testproject/versions/1.0/platform">
  <platformTroveName />
  <label/>
  <platformVersion></platformVersion>
  <productVersion>1.0</productVersion>
  <platformName>localhost@rpath:plat-1</platformName>
</platform>
"""
        self.assertXMLEquals(response, exp)

    def testSetImageDefinitions(self):
        uriTemplate = 'products/%s/versions/%s/imageDefinitions'
        uri = uriTemplate % (self.productShortName, self.productVersion)

        client = self.getRestClient(username='foouser', admin=True)
        req, response = client.call('PUT', uri, convert = True, body=imageSet1)

        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<imageDefinitions>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/71a60de01b7e8675254175584fdb9db2">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="6789" installLabelPath="" natNetworking="false" swapSize="512" vmMemory="64"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/201264007ec0d331b626ca074a841fa7">
    <name>virtual_irony 32-bit</name>
    <displayName>virtual_irony 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
      <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/24597af6ccdf86fbfdc1b011f61e8204">
    <name>update iso 64-bit</name>
    <displayName>update iso 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" freespace="2048" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false" swapSize="512"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
  </imageDefinition>
  <imageDefinition id="http://localhost:8000/api/products/testproject/versions/1.0/imageDefinitions/2ebe0a8a2711b1fd9c45a4a54783d958">
    <name>Old UI image that has an extra generic flavor in it</name>
    <displayName>Old UI image that has an extra generic flavor in it</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://localhost:8000/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
      <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" freespace="2048" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false" swapSize="512"/>
    </container>
    <architecture id="http://localhost:8000/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
  </imageDefinition>
</imageDefinitions>
"""
        self.assertXMLEquals(response,
            exp % dict(server = client.server, port = client.port))

        # Make sure we're fetching the same thing
        req, response = client.call('GET', uri, convert=True)
        self.failUnlessEqual(response,
            exp % dict(server = client.server, port = client.port))


    def testCreateProductVersion(self):
        productName = "blahblah"
        productDescription = productName * 2

        uriTemplate = 'products'
        uri = uriTemplate
        client = self.getRestClient(admin = True, username='foouser')

        req, response = client.call('POST', uri, body=newProduct1 % dict(
                name = productName,
                description = productDescription),
                convert=True)
        newUri = 'http://localhost:8000/api/products/%s' % productName
        self.failUnless(('id="%s"' % newUri) in response)

        productVersion = '3.0'

        uriTemplate = 'products/%s/versions'
        uri = uriTemplate % (productName, )

        req, response = client.call('POST', uri, body=newProductVersion1
                % dict(version = productVersion),
                convert=True)
        newUri = ("http://localhost:8000/api/products/%s/versions/%s"
                  % (productName, productVersion))
        self.failUnless(('id="%s"' % newUri) in response)

    def testGetProducts(self):
        return self._testGetProducts()

    def testGetProductsNotLoggedIn(self):
        return self._testGetProducts(notLoggedIn = True)

    def _testGetProducts(self, notLoggedIn = False):

        uriTemplate = 'products'
        uri = uriTemplate
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        else:
            self.createUser('foouser2')
            kw['username'] = 'foouser2'
        client = self.getRestClient(**kw)
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<products>
  <product id="http://%(server)s:%(port)s/api/products/testproject">
    <productId>1</productId>
    <hostname>testproject</hostname>
    <name>Project 1</name>
    <nameSpace>yournamespace</nameSpace>
    <domainname>rpath.local2</domainname>
    <shortname>testproject</shortname>
    <projecturl></projecturl>
    <repositoryHostname>testproject.rpath.local2</repositoryHostname>
    <repositoryUrl href="http://%(server)s:%(port)s/repos/testproject/api"/>
    <repositoryBrowserUrl href="http://%(server)s:%(port)s/repos/testproject/browse"/>
    <description></description>
    <prodtype>Appliance</prodtype>
    <commitEmail></commitEmail>
    <backupExternal>false</backupExternal>
    <timeCreated></timeCreated>
    <timeModified></timeModified>
    <hidden>false</hidden>
    <versions href="http://%(server)s:%(port)s/api/products/testproject/versions/"/>
    <members href="http://%(server)s:%(port)s/api/products/testproject/members/"/>
    <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
    <releases href="http://%(server)s:%(port)s/api/products/testproject/releases/"/>
    <images href="http://%(server)s:%(port)s/api/products/testproject/images/"/>
  </product>
</products>
"""
        resp = response
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            resp)
        self.assertBlobEquals(resp,
                exp % dict(port = client.port, server = client.server))

    def testGetOneProduct(self):
        return self._testGetProducts()

    def testGetOneProductNotLoggedIn(self):
        return self._testGetOneProduct(notLoggedIn = True)

    def _testGetOneProduct(self, notLoggedIn = False):

        uriTemplate = 'products/testproject'
        uri = uriTemplate
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        else:
            self.createUser('foouser')
            kw['username'] = 'foouser'
        client = self.getRestClient(**kw)
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<product id="http://%(server)s:%(port)s/api/products/testproject">
  <productId>1</productId>
  <hostname>testproject</hostname>
  <name>Project 1</name>
  <nameSpace>yournamespace</nameSpace>
  <domainname>rpath.local2</domainname>
  <shortname>testproject</shortname>
  <projecturl></projecturl>
  <repositoryHostname>testproject.rpath.local2</repositoryHostname>
  <repositoryUrl href="http://%(server)s:%(port)s/repos/testproject/api"/>
  <repositoryBrowserUrl href="http://%(server)s:%(port)s/repos/testproject/browse"/>
  <description></description>
  <prodtype>Appliance</prodtype>
  <commitEmail></commitEmail>
  <backupExternal>false</backupExternal>
  <timeCreated></timeCreated>
  <timeModified></timeModified>
  <hidden>false</hidden>
  <versions href="http://%(server)s:%(port)s/api/products/testproject/versions/"/>
  <members href="http://%(server)s:%(port)s/api/products/testproject/members/"/>
  <creator href="http://%(server)s:%(port)s/api/users/adminuser">adminuser</creator>
  <releases href="http://%(server)s:%(port)s/api/products/testproject/releases/"/>
  <images href="http://%(server)s:%(port)s/api/products/testproject/images/"/>
</product>
"""
        resp = response
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server))

    def testGetProductVersions(self):
        return self._testGetProductVersions()

    def testGetProductVersionsNotLoggedIn(self):
        return self._testGetProductVersions(notLoggedIn = True)

    def _testGetProductVersions(self, notLoggedIn = False):

        uriTemplate = 'products/testproject/versions'
        uri = uriTemplate
        kw = {}
        if notLoggedIn:
            kw['username'] = None
        else:
            self.createUser('foouser')
            kw['username'] = 'foouser'
        client = self.getRestClient(**kw)
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<productVersions>
  <productVersion id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0">
    <versionId>1</versionId>
    <hostname>testproject</hostname>
    <name>1.0</name>
    <productUrl href="http://%(server)s:%(port)s/api/products/testproject"/>
    <nameSpace>yournamespace</nameSpace>
    <description>Version description</description>
    <timeCreated></timeCreated>
    <platform href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/platform"/>
    <stages href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/"/>
    <definition href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/definition"/>
    <imageTypeDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions"/>
    <imageDefinitions href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions"/>
    <images href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/images"/>
    <sourceGroup>group-testproject-appliance</sourceGroup>
  </productVersion>
</productVersions>
"""
        resp = response
        for pat in [ "timeCreated", "timeModified" ]:
            resp = re.sub("<%s>.*</%s>" % (pat, pat),
             "<%s></%s>" % (pat, pat),
            resp)
        self.failUnlessEqual(resp,
             exp % dict(port = client.port, server = client.server))



imageSet1 = """
<imageDefinitions>
  <imageDefinition>
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit Edited for Completeness</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <options autoResolve="false" freespace="6789" natNetworking="false" vmMemory="64" swapSize="512" installLabelPath="" baseFileName=""/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64"/>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
    </flavorSet>
  </imageDefinition>
  <imageDefinition>
    <name>virtual_irony 32-bit</name>
    <displayName>Virtual Irony 32-bit</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="1024"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86" />
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
    </flavorSet>
  </imageDefinition>
  <imageDefinition>
    <name>update iso 64-bit</name>
    <displayName>update iso 64-bit</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="2048"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64" />
  </imageDefinition>
  <imageDefinition>
    <name>Old UI image that has an extra generic flavor in it</name>
    <displayName>Old UI image that has an extra generic flavor in it</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="2048"/>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86" />
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
    </flavorSet>
  </imageDefinition>
</imageDefinitions>
"""

newProduct1 = """
<product>
  <hostname>%(name)s</hostname>
  <name>%(name)s</name>
  <shortname>%(name)s</shortname>
  <description>%(description)s</description>
</product>
"""

newProductVersion1 = """
<productVersion>
  <description />
  <hostname />
  <id />
  <name>%(version)s</name>
  <nameSpace />
</productVersion>
"""

promoteGroup = """
<trove>
  <hostname />
  <name>group-%(name)s-appliance</name>
  <version>/testproject.rpath.local2@yournamespace:testproject-1.0-devel/1-2-1</version>
  <label>testproject.rpath.local2@yournamespace:testproject-1.0-devel</label>
  <trailingVersion />
  <flavor>~!dom0,~!domU,vmware,~!xen is: x86(i486,i586,i686,sse,sse2)</flavor>
  <timestamp />
  <images />
</trove>
"""


if __name__ == "__main__":
        testsetup.main()
