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

from  mint.rest.api import models

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
  <label>testproject.rpath.local2@yournamespace:testproject-1.0</label>
  <platform href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/platform"/>
  <platformVersion href="http://localhost:8000/api/products/testproject/versions/1.0/platformVersion"/>
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
        exp = exp % dict(port = client.port, server = client.server)
        self.assertXMLEquals(resp, exp)

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
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/bf19565548bcf6c28712a60cb02a808d">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/6471e079080cb3d767e81c4ef112c1da">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/e9ab1e72b797d11ce4f6b98e92aeee2f">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/100f456aff2280f146c8bfbdb5be8fdf">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
  </imageDefinition>
</imageDefinitions>
"""
        self.assertXMLEquals(response,
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
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/bf19565548bcf6c28712a60cb02a808d">
    <name>Citrix XenServer 32-bit</name>
    <displayName>Citrix XenServer 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/6471e079080cb3d767e81c4ef112c1da">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/e9ab1e72b797d11ce4f6b98e92aeee2f">
    <name>VMware ESX 32-bit</name>
    <displayName>VMware ESX 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/100f456aff2280f146c8bfbdb5be8fdf">
    <name>VMware ESX 64-bit</name>
    <displayName>VMware ESX 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
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
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/ce165212d22ca8ed80b5acb4b0fa58de">
    <name>ami_large</name>
    <displayName>EC2 AMI Large/Huge</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/amiImage">
      <name>amiImage</name>
      <displayName>Amazon Machine Image (EC2)</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/ami">
      <name>ami</name>
      <displayName>AMI</displayName>
    </flavorSet>
    <options amiHugeDiskMountpoint="False" autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="1024"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/amiImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/b9ffaaafacae3b42f72864d113d7995c">
    <name>ec2_small</name>
    <displayName>EC2 AMI Small</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/amiImage">
      <name>amiImage</name>
      <displayName>Amazon Machine Image (EC2)</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/ami">
      <name>ami</name>
      <displayName>AMI</displayName>
    </flavorSet>
    <options amiHugeDiskMountpoint="False" autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="1024"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/amiImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/ac0063910f7134cc838281b7fb5d42c2">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/applianceIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/693912898a7deda5fba2e11da496e31c">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/installableIsoImage">
      <name>installableIsoImage</name>
      <displayName>Legacy Installable CD/DVD</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/installableIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/00ce8ec04c049013d2d032a7d59b4353">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/updateIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/e9b231d3812e4ec7808c1b56d700f933">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/applianceIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/efab84338c2862b8d04fd3783a3394e9">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/installableIsoImage">
      <name>installableIsoImage</name>
      <displayName>Legacy Installable CD/DVD</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/installableIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/270978cfe105c57aff7eb3569717da2b">
    <name>iso</name>
    <displayName>ISO</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/updateIsoImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/4375b6b1a1607aa176d2adf29acdf83a">
    <name>hyper_v</name>
    <displayName>MS Hyper-V</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vhdImage">
      <name>vhdImage</name>
      <displayName>VHD for Microsoft(R) Hyper-V(R)</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
      <name>generic</name>
      <displayName>Generic</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vhdImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/a23df9b49d9fa36664c2d4009a457e23">
    <name>hyper_v</name>
    <displayName>MS Hyper-V</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vhdImage">
      <name>vhdImage</name>
      <displayName>VHD for Microsoft(R) Hyper-V(R)</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
      <name>generic</name>
      <displayName>Generic</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vhdImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/cf16e2998c6b727dd96b4fd923a2c5e1">
    <name>raw_fs</name>
    <displayName>Raw Filesystem</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawFsImage">
      <name>rawFsImage</name>
      <displayName>Eucalyptus/Mountable Filesystem</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/rawFsImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/dece8286c53268d424f719606a9182ec">
    <name>raw_fs</name>
    <displayName>Raw Filesystem</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawFsImage">
      <name>rawFsImage</name>
      <displayName>Eucalyptus/Mountable Filesystem</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/rawFsImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/6b9ec3e88b39e5f7db1e81ed5f5d1ef0">
    <name>raw_hd</name>
    <displayName>Raw Hard Disk</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawHdImage">
      <name>rawHdImage</name>
      <displayName>KVM/Parallels/QEMU/Raw Hard Disk</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/rawHdImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/287c7becce8de890d5b1626dd429eb47">
    <name>raw_hd</name>
    <displayName>Raw Hard Disk</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/rawHdImage">
      <name>rawHdImage</name>
      <displayName>KVM/Parallels/QEMU/Raw Hard Disk</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/rawHdImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/48bb9ca059314422f9cc0f09afb65976">
    <name>tar</name>
    <displayName>Tar Image</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/tarballImage">
      <name>tarballImage</name>
      <displayName>TAR File</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" installLabelPath="" swapSize="0"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/tarballImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/1e297fa23928806462908182ada781a0">
    <name>tar</name>
    <displayName>Tar Image</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/tarballImage">
      <name>tarballImage</name>
      <displayName>TAR File</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options autoResolve="false" baseFileName="" installLabelPath="" swapSize="0"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/tarballImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/0f1ead937e2152c31c2cdaa4f350a25f">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareImage">
      <name>vmwareImage</name>
      <displayName>VMware(R) Workstation/Fusion Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" diskAdapter="lsilogic" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/4599da97777a0ef9208c831872f65e1a">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/5fbfbac74be1703761d5f4d843aca4d1">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareImage">
      <name>vmwareImage</name>
      <displayName>VMware(R) Workstation/Fusion Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" diskAdapter="lsilogic" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256" vmSnapshots="false"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/14e2f46bc7d83b95300b17dded8d1c4c">
    <name>vmware</name>
    <displayName>VMware</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/vmwareEsxImage">
      <name>vmwareEsxImage</name>
      <displayName>VMware(R) ESX/VCD Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/vmware">
      <name>vmware</name>
      <displayName>VMware</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" natNetworking="true" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/vmwareEsxImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/d0bf5e94df8c729839c2b3a50d8e5b34">
    <name>virtual_iron</name>
    <displayName>Virtual Iron</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/virtualIronImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/124a6b3c25ee6f1d07530cb751ac15bb">
    <name>virtual_iron</name>
    <displayName>Virtual Iron</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/virtualIronImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/2560dae479b4fe726ac0429de3a72c5c">
    <name>xen_ova</name>
    <displayName>Xen OVA</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageTypeDefinition>
  <imageTypeDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageTypeDefinitions/acd0dc888ab70e27d38447365fcb9f56">
    <name>xen_ova</name>
    <displayName>Xen OVA</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vmMemory="256"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
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
        platformVersion = models.PlatformVersion(
            name="foo", revision="foo", label="foo", version="foo",
            ordering="foo", _platformId="2")
        mock.mock(platformmgr.Platforms, 'getPlatformVersions',
            platformVersion)
        uriTemplate = 'products/%s/versions/%s/platformVersion'
        uri = uriTemplate % (self.productShortName, self.productVersion)
        client = self.getRestClient(username='foouser', admin=True)

        label = 'localhost@rpath:plat-2'
        data = """\
<platformVersion>
  <label>%s</label>
  <name>rebase-to-latest-on-versionless-platform</name>
</platformVersion>
""" % label
        req, response = client.call('PUT', uri, data, convert = True)
        expected = """\
<platformVersion id="http://localhost:8000/api/platforms/2/platformVersions/foo%3Dfoo">
  <name>foo</name>
  <version>foo</version>
  <revision>foo</revision>
  <label>foo</label>
  <ordering>foo</ordering>
</platformVersion>
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
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/dd09ba2ba7ad71c756bdf79dca0ec331">
    <name>Citrix XenServer 64-bit</name>
    <displayName>Citrix XenServer 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage">
      <name>xenOvaImage</name>
      <displayName>Citrix(R) XenServer(TM) Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
      <name>xen</name>
      <displayName>Xen</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="6789" installLabelPath="" natNetworking="false" swapSize="512" vmMemory="64"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/f529d60760c1d1b0250bbe5787a9f661">
    <name>virtual_irony 32-bit</name>
    <displayName>virtual_irony 32-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage">
      <name>virtualIronImage</name>
      <displayName>Virtual Iron Virtual Appliance</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
      <name>virtual_iron</name>
      <displayName>Virtual Iron</displayName>
    </flavorSet>
    <options autoResolve="false" baseFileName="" freespace="1024" installLabelPath="" swapSize="512" vhdDiskType="dynamic"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/virtualIronImage"/>
  </imageDefinition>
  <imageDefinition id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/imageDefinitions/23b4aba399fd29e9f28aac7a0c16d0ae">
    <name>update iso 64-bit</name>
    <displayName>update iso 64-bit</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage">
      <name>updateIsoImage</name>
      <displayName>Update CD/DVD</displayName>
    </container>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64">
      <name>x86_64</name>
      <displayName>x86 (64-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" freespace="2048" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/updateIsoImage"/>
  </imageDefinition>
  <imageDefinition id="http://localhost:8000/api/products/testproject/versions/1.0/imageDefinitions/007a4984a99129d86084918e09bfaf42">
    <name>Old UI image that has an extra generic flavor in it</name>
    <displayName>Old UI image that has an extra generic flavor in it</displayName>
    <imageGroup>group-testproject-appliance</imageGroup>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/Development"/>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/QA"/>
    <stage href="http://localhost:8000/api/products/testproject/versions/1.0/stages/Release"/>
    <container id="http://localhost:8000/api/products/testproject/versions/1.0/containers/applianceIsoImage">
      <name>applianceIsoImage</name>
      <displayName>Appliance Installable ISO</displayName>
    </container>
    <architecture id="http://localhost:8000/api/products/testproject/versions/1.0/architectures/x86">
      <name>x86</name>
      <displayName>x86 (32-bit)</displayName>
    </architecture>
    <options anacondaCustomTrove="" anacondaTemplatesTrove="conary.rpath.com@rpl:2" autoResolve="false" baseFileName="" betaNag="false" bugsUrl="" freespace="2048" installLabelPath="" mediaTemplateTrove="" showMediaCheck="false" swapSize="512"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/applianceIsoImage"/>
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
    <description></description>
    <prodtype>Appliance</prodtype>
    <commitEmail></commitEmail>
    <backupExternal>false</backupExternal>
    <timeCreated></timeCreated>
    <timeModified></timeModified>
    <hidden>false</hidden>
    <role>User</role>
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
  <description></description>
  <prodtype>Appliance</prodtype>
  <commitEmail></commitEmail>
  <backupExternal>false</backupExternal>
  <timeCreated></timeCreated>
  <timeModified></timeModified>
  <hidden>false</hidden>
  <role>User</role>
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
        self.assertXMLEquals(resp,
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
    <platformVersion href="http://localhost:8000/api/products/testproject/versions/1.0/platformVersion"/>
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
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/xenOvaImage"/>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64"/>
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/xen">
    </flavorSet>
    <options autoResolve="false" freespace="6789" natNetworking="false" vmMemory="64" swapSize="512" installLabelPath="" baseFileName=""/>
  </imageDefinition>
  <imageDefinition>
    <name>virtual_irony 32-bit</name>
    <displayName>Virtual Irony 32-bit</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/virtualIronImage"/>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86" />
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/virtual_iron">
    </flavorSet>
    <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="1024"/>
  </imageDefinition>
  <imageDefinition>
    <name>update iso 64-bit</name>
    <displayName>update iso 64-bit</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/updateIsoImage"/>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86_64" />
    <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="2048"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/updateIsoImage"/>
  </imageDefinition>
  <imageDefinition>
    <name>Old UI image that has an extra generic flavor in it</name>
    <displayName>Old UI image that has an extra generic flavor in it</displayName>
    <container id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/containers/applianceIsoImage"/>
    <architecture id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/architectures/x86" />
    <flavorSet id="http://%(server)s:%(port)s/api/products/testproject/versions/1.0/flavorSets/generic">
    </flavorSet>
    <options autoResolve="false" installLabelPath="" baseFileName="" swapSize="512" freespace="2048"/>
    <descriptor id="http://%(server)s:%(port)s/api/v1/platforms/image_type_definition_descriptors/xenOvaImage"/>
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
