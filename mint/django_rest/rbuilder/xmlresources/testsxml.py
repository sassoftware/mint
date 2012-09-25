#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

schema_and_data_validxml1_xml = """\
  <xml_resource>
    <schema>&lt;xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema"&gt; &lt;xs:element name="validation_report" type="ConfigValidationReport"/&gt; &lt;xs:element name="discovery_report" type="ConfigDiscoveryReport"/&gt; &lt;xs:element name="read_report" type="ConfigReadReport"/&gt; &lt;xs:complexType name="ConfigValidationReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigDiscoveryReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigReadReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigError"&gt; &lt;xs:all&gt; &lt;xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigErrors"&gt; &lt;xs:sequence&gt; &lt;xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigCheck"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigChecks"&gt; &lt;xs:sequence&gt; &lt;xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperty"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperties"&gt; &lt;xs:sequence&gt; &lt;xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:simpleType name="Version"&gt; &lt;xs:restriction base="xs:decimal"&gt; &lt;xs:enumeration value="2"/&gt; &lt;xs:enumeration value="2.0"/&gt; &lt;/xs:restriction&gt; &lt;/xs:simpleType&gt; &lt;/xs:schema&gt;</schema>
    <xml>&lt;validation_report version="2" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt; &lt;name&gt;apache_configuration&lt;/name&gt; &lt;display_name&gt;Apache Configuration Validator&lt;/display_name&gt; &lt;success&gt;true&lt;/success&gt; &lt;summary&gt;Apache report summary&lt;/summary&gt; &lt;details&gt;Apache report details&lt;/details&gt; &lt;errors&gt; &lt;error&gt; &lt;code&gt;500&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Apache not started]]&gt;&lt;/details&gt; &lt;summary&gt;General error: apache not running&lt;/summary&gt; &lt;/error&gt; &lt;error&gt; &lt;code&gt;1&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Traceback: A bunch of tb data]]&gt;&lt;/details&gt; &lt;summary&gt;Error when stuff broke, fix it&lt;/summary&gt; &lt;/error&gt; &lt;/errors&gt; &lt;checks&gt; &lt;check&gt; &lt;summary&gt;Apache not running on port&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache Port check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Port Check&lt;/display_name&gt; &lt;name&gt;port_check&lt;/name&gt; &lt;success&gt;false&lt;/success&gt; &lt;/check&gt; &lt;check&gt; &lt;summary&gt;Apache debug 5&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache debug check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Debug Check&lt;/display_name&gt; &lt;name&gt;debug_check&lt;/name&gt; &lt;success&gt;true&lt;/success&gt; &lt;/check&gt; &lt;/checks&gt; &lt;/validation_report&gt;</xml> 
  </xml_resource>
"""

schema_and_data_validxml2_xml = """\
  <xml_resource>
    <schema>&lt;xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema"&gt; &lt;xs:element name="validation_report" type="ConfigValidationReport"/&gt; &lt;xs:element name="discovery_report" type="ConfigDiscoveryReport"/&gt; &lt;xs:element name="read_report" type="ConfigReadReport"/&gt; &lt;xs:complexType name="ConfigValidationReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigDiscoveryReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigReadReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigError"&gt; &lt;xs:all&gt; &lt;xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigErrors"&gt; &lt;xs:sequence&gt; &lt;xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigCheck"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigChecks"&gt; &lt;xs:sequence&gt; &lt;xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperty"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperties"&gt; &lt;xs:sequence&gt; &lt;xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:simpleType name="Version"&gt; &lt;xs:restriction base="xs:decimal"&gt; &lt;xs:enumeration value="2"/&gt; &lt;xs:enumeration value="2.0"/&gt; &lt;/xs:restriction&gt; &lt;/xs:simpleType&gt; &lt;/xs:schema&gt;</schema> 
    <xml>&lt;validation_report version="2" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt; &lt;name&gt;apache_configuration&lt;/name&gt; &lt;display_name&gt;Apache Configuration Validator&lt;/display_name&gt; &lt;success&gt;true&lt;/success&gt; &lt;summary&gt;Apache report summary&lt;/summary&gt; &lt;details&gt;Apache report details&lt;/details&gt; &lt;errors&gt; &lt;error&gt; &lt;code&gt;500&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Apache not started]]&gt;&lt;/details&gt; &lt;summary&gt;General error: apache not running&lt;/summary&gt; &lt;/error&gt; &lt;error&gt; &lt;code&gt;1&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Traceback: A bunch of tb data]]&gt;&lt;/details&gt; &lt;summary&gt;Error when stuff broke, fix it&lt;/summary&gt; &lt;/error&gt; &lt;/errors&gt; &lt;checks&gt; &lt;check&gt; &lt;summary&gt;Apache not running on port&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache Port check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Port Check&lt;/display_name&gt; &lt;name&gt;port_check&lt;/name&gt; &lt;success&gt;false&lt;/success&gt; &lt;/check&gt; &lt;check&gt; &lt;summary&gt;Apache debug 5&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache debug check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Debug Check&lt;/display_name&gt; &lt;name&gt;debug_check&lt;/name&gt; &lt;success&gt;true&lt;/success&gt; &lt;/check&gt; &lt;/checks&gt; &lt;/validation_report&gt;</xml> 
  </xml_resource>
"""

schema_and_data_validxml3_xml = """\
<xml_resource> 
    <schema>&lt;xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema"&gt; &lt;xs:element name="validation_report" type="ConfigValidationReport"/&gt; &lt;xs:element name="discovery_report" type="ConfigDiscoveryReport"/&gt; &lt;xs:element name="read_report" type="ConfigReadReport"/&gt; &lt;xs:complexType name="ConfigValidationReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigDiscoveryReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigReadReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigError"&gt; &lt;xs:all&gt; &lt;xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigErrors"&gt; &lt;xs:sequence&gt; &lt;xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigCheck"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigChecks"&gt; &lt;xs:sequence&gt; &lt;xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperty"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperties"&gt; &lt;xs:sequence&gt; &lt;xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:simpleType name="Version"&gt; &lt;xs:restriction base="xs:decimal"&gt; &lt;xs:enumeration value="2"/&gt; &lt;xs:enumeration value="2.0"/&gt; &lt;/xs:restriction&gt; &lt;/xs:simpleType&gt; &lt;/xs:schema&gt;</schema> 
    <xml>&lt;validation_report version="2" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt; &lt;name&gt;apache_configuration&lt;/name&gt; &lt;display_name&gt;Apache Configuration Validator&lt;/display_name&gt; &lt;success&gt;true&lt;/success&gt; &lt;summary&gt;Apache report summary&lt;/summary&gt; &lt;details&gt;Apache report details&lt;/details&gt; &lt;errors&gt; &lt;error&gt; &lt;code&gt;500&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Apache not started]]&gt;&lt;/details&gt; &lt;summary&gt;General error: apache not running&lt;/summary&gt; &lt;/error&gt; &lt;error&gt; &lt;code&gt;1&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Traceback: A bunch of tb data]]&gt;&lt;/details&gt; &lt;summary&gt;Error when stuff broke, fix it&lt;/summary&gt; &lt;/error&gt; &lt;/errors&gt; &lt;checks&gt; &lt;check&gt; &lt;summary&gt;Apache not running on port&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache Port check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Port Check&lt;/display_name&gt; &lt;name&gt;port_check&lt;/name&gt; &lt;success&gt;false&lt;/success&gt; &lt;/check&gt; &lt;check&gt; &lt;summary&gt;Apache debug 5&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache debug check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Debug Check&lt;/display_name&gt; &lt;name&gt;debug_check&lt;/name&gt; &lt;success&gt;true&lt;/success&gt; &lt;/check&gt; &lt;/checks&gt; &lt;/validation_report&gt;</xml> 
</xml_resource>
"""

schema_and_data_invalidxml1_xml = """\
  <xml_resource>
    <schema><![CDATA[<?xml version="1.0" encoding="utf-8"?> <xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema">  <!-- rPath configuration top level elements --> <xs:element name="validation_report" type="ConfigValidationReport"></xs:element> <xs:element name="discovery_report" type="ConfigDiscoveryReport"></xs:element> <xs:element name="read_report" type="ConfigReadReport"></xs:element>  <!-- Validation report complex type --> <xs:complexType name="ConfigValidationReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element>  <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element>  <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Discovery report complex type --> <xs:complexType name="ConfigDiscoveryReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Read report complex type --> <xs:complexType name="ConfigReadReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Generic complex types --> <xs:complexType name="ConfigError"> <xs:all> <xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigErrors"> <xs:sequence> <xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigCheck"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigChecks"> <xs:sequence> <xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigProperty"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigProperties"> <xs:sequence> <xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:simpleType name="Version"> <xs:restriction base="xs:decimal"> <xs:enumeration value="2"/> <xs:enumeration value="2.0"/> </xs:restriction> </xs:simpleType> </xs:schema>]]></schema>
    <xml><![CDATA[validation_report version="2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd"> <name>cim_configuration</name> <display_name>Apache Configuration Validator</display_name> <success>true</success> <summary>CIM report summary</summary> <details>CIM report details</details> <checks> <check> <summary>Running</summary> <details>CIM Service Check output here</details> <display_name>CIM Service Check</display_name> <name>cim_check</name> <success>true</success> </check> </checks> </validation_report>]]></xml>
  </xml_resource>
"""

schema_and_data_invalidxml2_xml = """\
  <xml_resource />
"""

schema_and_data_invalidschema1_xml = """\
  <xml_resource>
    <schema><![CDATA[<?xml version="1.0" encoding="utf-8"?> <xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema">  <!-- rPath configuration top level elements --> <xs:element name="validation_report" type="ConfigValidationReport"></xs:element> <xs:element name="discovery_report" type="ConfigDiscoveryReport"></xs:element> <xs:element name="read_report" type="ConfigReadReport"></xs:element>  <!-- Validation report complex type --> <xs:complexType name="ConfigValidationReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element>  <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element>  <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Discovery report complex type --> <xs:complexType name="ConfigDiscoveryReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Read report complex type --> <xs:complexType name="ConfigReadReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Generic complex types --> <xs:complexType name="ConfigError"> <xs:all> <xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigErrors"> <xs:sequence> <xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigCheck"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigChecks"> <xs:sequence> <xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigProperty"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigProperties"> <xs:sequence> <xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:simpleType name="Version"> <xs:restriction base="xs:decimal"> <xs:enumeration value="2"/> <xs:enumeration value="2.0"/> </xs:restriction> </xs:simpleType> </xs:schema>]]></schema>
    <xml><![CDATA[validation_report version="2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd"> <display_name>Apache Configuration Validator</display_name> <success>true</success> <summary>CIM report summary</summary> <details>CIM report details</details> <checks> <check> <summary>Running</summary> <details>CIM Service Check output here</details> <display_name>CIM Service Check</display_name> <name>cim_check</name> <success>true</success> </check> </checks> </validation_report>]]></xml>
  </xml_resource>
"""

schema_and_data_invalidschema2_xml = """\
  <xml_resource>
    <schema><![CDATA[<?xml version="1.0" encoding="utf-8"?> <xs:schema id="rPathConfigurator" xmlns:xs="http://www.w3.org/2001/XMLSchema">  <!-- rPath configuration top level elements --> <xs:element name="validation_report" type="ConfigValidationReport"></xs:element> <xs:element name="discovery_report" type="ConfigDiscoveryReport"></xs:element> <xs:element name="read_report" type="ConfigReadReport"></xs:element>  <!-- Validation report complex type --> <xs:complexType name="ConfigValidationReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element>  <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element>  <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Discovery report complex type --> <xs:complexType name="ConfigDiscoveryReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Read report complex type --> <xs:complexType name="ConfigReadReport"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"></xs:element> <xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"></xs:element> </xs:all>  <xs:attribute name="version" type="Version" use="required"></xs:attribute> </xs:complexType>  <!-- Generic complex types --> <xs:complexType name="ConfigError"> <xs:all> <xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigErrors"> <xs:sequence> <xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigCheck"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigChecks"> <xs:sequence> <xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:complexType name="ConfigProperty"> <xs:all> <xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"></xs:element> <xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"></xs:element> </xs:all> </xs:complexType>  <xs:complexType name="ConfigProperties"> <xs:sequence> <xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"></xs:element> </xs:sequence> </xs:complexType>  <xs:simpleType name="Version"> <xs:restriction base="xs:decimal"> <xs:enumeration value="2"/> <xs:enumeration value="2.0"/> </xs:restriction> </xs:simpleType> </xs:schema>]]></schema>
    <xml><![CDATA[<validation_report version="5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd"> <name>cim_configuration</name> <display_name>Apache Configuration Validator</display_name> <success>true</success> <summary>CIM report summary</summary> <details>CIM report details</details> <checks> <check> <summary>Running</summary> <details>CIM Service Check output here</details> <display_name>CIM Service Check</display_name> <name>cim_check</name> <success>true</success> </check> </checks> </validation_report>]]></xml>
  </xml_resource>
"""

schema_and_data_hanging_xml = """\
<xml_resource>
  <schema>&lt;xs:schema id="rPathConfigurator" targetNamespace="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd" xmlns:xs="http://www.w3.org/2001/XMLSchema"&gt; &lt;xs:element name="validation_report" type="ConfigValidationReport"/&gt; &lt;xs:element name="discovery_report" type="ConfigDiscoveryReport"/&gt; &lt;xs:element name="read_report" type="ConfigReadReport"/&gt; &lt;xs:complexType name="ConfigValidationReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="checks" type="ConfigChecks" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigDiscoveryReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="result" type="xs:string" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigReadReport"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="errors" type="ConfigErrors" maxOccurs="1" minOccurs="0"/&gt; &lt;xs:element name="properties" type="ConfigProperties" maxOccurs="1" minOccurs="0"/&gt; &lt;/xs:all&gt; &lt;xs:attribute name="version" type="Version" use="required"/&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigError"&gt; &lt;xs:all&gt; &lt;xs:element name="code" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigErrors"&gt; &lt;xs:sequence&gt; &lt;xs:element name="error" type="ConfigError" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigCheck"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="display_name" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="summary" type="xs:normalizedString" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="details" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="success" type="xs:boolean" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigChecks"&gt; &lt;xs:sequence&gt; &lt;xs:element name="check" type="ConfigCheck" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperty"&gt; &lt;xs:all&gt; &lt;xs:element name="name" type="xs:Name" maxOccurs="1" minOccurs="1"/&gt; &lt;xs:element name="value" type="xs:string" maxOccurs="1" minOccurs="1"/&gt; &lt;/xs:all&gt; &lt;/xs:complexType&gt; &lt;xs:complexType name="ConfigProperties"&gt; &lt;xs:sequence&gt; &lt;xs:element name="property" type="ConfigProperty" maxOccurs="unbounded" minOccurs="0"/&gt; &lt;/xs:sequence&gt; &lt;/xs:complexType&gt; &lt;xs:simpleType name="Version"&gt; &lt;xs:restriction base="xs:decimal"&gt; &lt;xs:enumeration value="2"/&gt; &lt;xs:enumeration value="2.0"/&gt; &lt;/xs:restriction&gt; &lt;/xs:simpleType&gt; &lt;/xs:schema&gt;</schema>
  <xml>&lt;validation_report version="2" xsi:schemaLocation="http://www.rpath.com/permanent/rpath-configurator-2.0.xsd rpath-configurator-2.0.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt; &lt;name&gt;apache_configuration&lt;/name&gt; &lt;display_name&gt;Apache Configuration Validator&lt;/display_name&gt; &lt;success&gt;true&lt;/success&gt; &lt;summary&gt;Apache report summary&lt;/summary&gt; &lt;details&gt;Apache report details&lt;/details&gt; &lt;errors&gt; &lt;error&gt; &lt;code&gt;500&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Apache not started]]&gt;&lt;/details&gt; &lt;summary&gt;General error: apache not running&lt;/summary&gt; &lt;/error&gt; &lt;error&gt; &lt;code&gt;1&lt;/code&gt; &lt;details&gt;&lt;![CDATA[Traceback: A bunch of tb data]]&gt;&lt;/details&gt; &lt;summary&gt;Error when stuff broke, fix it&lt;/summary&gt; &lt;/error&gt; &lt;/errors&gt; &lt;checks&gt; &lt;check&gt; &lt;summary&gt;Apache not running on port&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache Port check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Port Check&lt;/display_name&gt; &lt;name&gt;port_check&lt;/name&gt; &lt;success&gt;false&lt;/success&gt; &lt;/check&gt; &lt;check&gt; &lt;summary&gt;Apache debug 5&lt;/summary&gt; &lt;details&gt;&lt;![CDATA[Apache debug check output here]]&gt;&lt;/details&gt; &lt;display_name&gt;Apache Debug Check&lt;/display_name&gt; &lt;name&gt;debug_check&lt;/name&gt; &lt;success&gt;true&lt;/success&gt; &lt;/check&gt; &lt;/checks&gt; &lt;/validation_report&gt;</xml>
</xml_resource>
"""
