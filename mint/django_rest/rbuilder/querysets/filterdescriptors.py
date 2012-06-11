#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#
system_filter_descriptor = """\
<?xml version="1.0"?>
<filter_descriptor id="@@ID@@">
	<field_descriptors>
		<field_descriptor>
			<field_description>the port used by the system's CIM broker</field_description>
			<field_key>agent_port</field_key>
			<field_label>agent_port</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>productId</field_description>
			<field_key>appliance.productId</field_key>
			<field_label>appliance.productId</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>hostname</field_description>
			<field_key>appliance.hostname</field_key>
			<field_label>appliance.hostname</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>appliance.name</field_key>
			<field_label>Appliance Name</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>namespace</field_description>
			<field_key>appliance.namespace</field_key>
			<field_label>appliance.namespace</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>domainname</field_description>
			<field_key>appliance.domainname</field_key>
			<field_label>appliance.domainname</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>shortname</field_description>
			<field_key>appliance.shortname</field_key>
			<field_label>Appliance Unique Name</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>projecturl</field_description>
			<field_key>appliance.projecturl</field_key>
			<field_label>appliance.projecturl</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>repositoryHostName</field_description>
			<field_key>appliance.repositoryHostName</field_key>
			<field_label>appliance.repositoryHostName</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>appliance.description</field_key>
			<field_label>appliance.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>prodtype</field_description>
			<field_key>appliance.prodtype</field_key>
			<field_label>appliance.prodtype</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>commitemail</field_description>
			<field_key>appliance.commitemail</field_key>
			<field_label>appliance.commitemail</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>backupexternal</field_description>
			<field_key>appliance.backupexternal</field_key>
			<field_label>appliance.backupexternal</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timecreated</field_description>
			<field_key>appliance.timecreated</field_key>
			<field_label>Appliance Created</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timemodified</field_description>
			<field_key>appliance.timemodified</field_key>
			<field_label>Appliance Modified</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>hidden</field_description>
			<field_key>appliance.hidden</field_key>
			<field_label>appliance.hidden</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>userid</field_description>
			<field_key>appliance.creatorid.userid</field_key>
			<field_label>appliance.creatorid.userid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>username</field_description>
			<field_key>appliance.creatorid.username</field_key>
			<field_label>Appliance Creator (Username)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>fullname</field_description>
			<field_key>appliance.creatorid.fullname</field_key>
			<field_label>Appliance Creator (Full Name)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>salt</field_description>
			<field_key>appliance.creatorid.salt</field_key>
			<field_label>appliance.creatorid.salt</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
<!--
		<field_descriptor>
			<field_description>passwd</field_description>
			<field_key>appliance.creatorid.passwd</field_key>
			<field_label>appliance creatorid passwd</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
-->
		<field_descriptor>
			<field_description>email</field_description>
			<field_key>appliance.creatorid.email</field_key>
			<field_label>appliance.creatorid.email</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>displayemail</field_description>
			<field_key>appliance.creatorid.displayemail</field_key>
			<field_label>appliance.creatorid.displayemail</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timecreated</field_description>
			<field_key>appliance.creatorid.timecreated</field_key>
			<field_label>appliance.creatorid.timecreated</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timeaccessed</field_description>
			<field_key>appliance.creatorid.timeaccessed</field_key>
			<field_label>appliance.creatorid.timeaccessed</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>active</field_description>
			<field_key>appliance.creatorid.active</field_key>
			<field_label>appliance.creatorid.active</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>blurb</field_description>
			<field_key>appliance.creatorid.blurb</field_key>
			<field_label>appliance.creatorid.blurb</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>configuration</field_description>
			<field_key>configuration</field_key>
			<field_label>configuration</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was added to inventory (UTC)</field_description>
			<field_key>created_date</field_key>
			<field_label>System Record Created</field_label>
			<basic_field>true</basic_field>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>credentials</field_description>
			<field_key>credentials</field_key>
			<field_label>credentials</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>system_state_id</field_description>
			<field_key>current_state.system_state_id</field_key>
			<field_label>current_state.system_state_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>current_state.name</field_key>
			<field_label>current_state.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>unmanaged</options>
				<options>unmanaged-credentials</options>
				<options>registered</options>
				<options>responsive</options>
				<options>non-responsive-unknown</options>
				<options>non-responsive-net</options>
				<options>non-responsive-host</options>
				<options>non-responsive-shutdown</options>
				<options>non-responsive-suspended</options>
				<options>non-responsive-credentials</options>
				<options>dead</options>
				<options>mothballed</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>current_state.description</field_key>
			<field_label>Management State</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>created_date</field_description>
			<field_key>current_state.created_date</field_key>
			<field_label>current_state.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system description</field_description>
			<field_key>description</field_key>
			<field_label>Description</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>a UUID that is randomly generated</field_description>
			<field_key>generated_uuid</field_key>
			<field_label>UUID (Generated)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system hostname</field_description>
			<field_key>hostname</field_key>
			<field_label>Hostname</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>trove_id</field_description>
			<field_key>installed_software.trove_id</field_key>
			<field_label>installed_software.trove_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>installed_software.name</field_key>
			<field_label>installed_software.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>version_id</field_description>
			<field_key>installed_software.version.version_id</field_key>
			<field_label>installed_software.version.version_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>full</field_description>
			<field_key>installed_software.version.full</field_key>
			<field_label>installed_software.version.full</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>label</field_description>
			<field_key>installed_software.version.label</field_key>
			<field_label>installed_software.version.label</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>revision</field_description>
			<field_key>installed_software.version.revision</field_key>
			<field_label>installed_software.version.revision</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>ordering</field_description>
			<field_key>installed_software.version.ordering</field_key>
			<field_label>installed_software.version.ordering</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>flavor</field_description>
			<field_key>installed_software.version.flavor</field_key>
			<field_label>installed_software.version.flavor</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>flavor</field_description>
			<field_key>installed_software.flavor</field_key>
			<field_label>installed_software.flavor</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>is_top_level</field_description>
			<field_key>installed_software.is_top_level</field_key>
			<field_label>installed_software.is_top_level</field_label>
			<value_type>bool</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>last_available_update_refresh</field_description>
			<field_key>installed_software.last_available_update_refresh</field_key>
			<field_label>installed_software.last_available_update_refresh</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>job_id</field_description>
			<field_key>jobs.job_id</field_key>
			<field_label>jobs.job_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>job_uuid</field_description>
			<field_key>jobs.job_uuid</field_key>
			<field_label>jobs.job_uuid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>job_state_id</field_description>
			<field_key>jobs.job_state.job_state_id</field_key>
			<field_label>jobs.job_state.job_state_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>jobs.job_state.name</field_key>
			<field_label>jobs.job_state name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>Queued</options>
				<options>Running</options>
				<options>Completed</options>
				<options>Failed</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>status_code</field_description>
			<field_key>jobs.status_code</field_key>
			<field_label>jobs.status_code</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>status_text</field_description>
			<field_key>jobs.status_text</field_key>
			<field_label>jobs.status_text</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>status_detail</field_description>
			<field_key>jobs.status_detail</field_key>
			<field_label>jobs.status_detail</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>event_type_id</field_description>
			<field_key>jobs.event_type.event_type_id</field_key>
			<field_label>jobs.event_type.event_type_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>jobs.event_type.name</field_key>
			<field_label>jobs.event_type.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>system registration</options>
				<options>immediate system poll</options>
				<options>system poll</options>
				<options>system apply update</options>
				<options>immediate system apply update</options>
				<options>system shutdown</options>
				<options>immediate system shutdown</options>
				<options>system launch wait</options>
				<options>system detect management interface</options>
				<options>immediate system detect management interface</options>
				<options>immediate system configuration</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>jobs.event_type.description</field_key>
			<field_label>jobs.event_type.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>priority</field_description>
			<field_key>jobs.event_type.priority</field_key>
			<field_label>jobs.event_type.priority</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>time_created</field_description>
			<field_key>jobs.time_created</field_key>
			<field_label>jobs.time_created</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>time_updated</field_description>
			<field_key>jobs.time_updated</field_key>
			<field_label>jobs.time_updated</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was deployed (only applies if system is on a virtual target)</field_description>
			<field_key>launch_date</field_key>
			<field_label>Launched</field_label>
			<basic_field>true</basic_field>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>userid</field_description>
			<field_key>launching_user.userid</field_key>
			<field_label>launching_user.userid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>username</field_description>
			<field_key>launching_user.username</field_key>
			<field_label>Launched By (Username)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>fullname</field_description>
			<field_key>launching_user.fullname</field_key>
			<field_label>Launched By (Full Name)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>salt</field_description>
			<field_key>launching_user.salt</field_key>
			<field_label>launching_user.salt</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>passwd</field_description>
			<field_key>launching_user.passwd</field_key>
			<field_label>launching_user.passwd</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>email</field_description>
			<field_key>launching_user.email</field_key>
			<field_label>launching_user.email</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>displayemail</field_description>
			<field_key>launching_user.displayemail</field_key>
			<field_label>launching_user.displayemail</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timecreated</field_description>
			<field_key>launching_user.timecreated</field_key>
			<field_label>launching_user.timecreated</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timeaccessed</field_description>
			<field_key>launching_user.timeaccessed</field_key>
			<field_label>launching_user.timeaccessed</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>active</field_description>
			<field_key>launching_user.active</field_key>
			<field_label>launching_user.active</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>blurb</field_description>
			<field_key>launching_user.blurb</field_key>
			<field_label>launching_user.blurb</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>a UUID created from the system hardware profile</field_description>
			<field_key>local_uuid</field_key>
			<field_label>UUID (Local)</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>productVersionId</field_description>
			<field_key>major_version.productVersionId</field_key>
			<field_label>major_version.productVersionId</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>namespace</field_description>
			<field_key>major_version.namespace</field_key>
			<field_label>major_version.namespace</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>major_version.name</field_key>
			<field_label>major_version.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>major_version.description</field_key>
			<field_label>major_version.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>timecreated</field_description>
			<field_key>major_version.timecreated</field_key>
			<field_label>major_version.timecreated</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the database ID for the management interface</field_description>
			<field_key>management_interface.management_interface_id</field_key>
			<field_label>management_interface.management_interface_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the name of the management interface</field_description>
			<field_key>management_interface.name</field_key>
			<field_label>management_interface.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>cim</options>
				<options>wmi</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>the description of the management interface</field_description>
			<field_key>management_interface.description</field_key>
			<field_label>management_interface.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the management interface was added to inventory (UTC)</field_description>
			<field_key>management_interface.created_date</field_key>
			<field_label>management_interface.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the port used by the management interface</field_description>
			<field_key>management_interface.port</field_key>
			<field_label>management_interface.port</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the descriptor of available fields to set credentials for the management interface</field_description>
			<field_key>management_interface.credentials_descriptor</field_key>
			<field_label>management_interface.credentials_descriptor</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>whether or not the management interface has readonly credentials</field_description>
			<field_key>management_interface.credentials_readonly</field_key>
			<field_label>management_interface.credentials_readonly</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the database ID for the system</field_description>
			<field_key>managementnode.system_id</field_key>
			<field_label>managementnode.system_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system name</field_description>
			<field_key>managementnode.name</field_key>
			<field_label>managementnode.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system description</field_description>
			<field_key>managementnode.description</field_key>
			<field_label>managementnode.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was added to inventory (UTC)</field_description>
			<field_key>managementnode.created_date</field_key>
			<field_label>managementnode.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system hostname</field_description>
			<field_key>managementnode.hostname</field_key>
			<field_label>managementnode.hostname</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was deployed (only applies if system is on a virtual target)</field_description>
			<field_key>managementnode.launch_date</field_key>
			<field_label>managementnode.launch_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targetid</field_description>
			<field_key>managementnode.target.targetid</field_key>
			<field_label>managementnode.target.targetid</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targettype</field_description>
			<field_key>managementnode.target.targettype</field_key>
			<field_label>managementnode.target.targettype</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targetname</field_description>
			<field_key>managementnode.target.targetname</field_key>
			<field_label>managementnode.target.targetname</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system ID as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>managementnode.target_system_id</field_key>
			<field_label>managementnode.target_system_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system name as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>managementnode.target_system_name</field_key>
			<field_label>managementnode.target_system_name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system description as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>managementnode.target_system_description</field_key>
			<field_label>managementnode.target_system_description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system state as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>managementnode.target_system_state</field_key>
			<field_label>managementnode.target_system_state</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was registered in inventory (UTC)</field_description>
			<field_key>managementnode.registration_date</field_key>
			<field_label>managementnode.registration_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>a UUID that is randomly generated</field_description>
			<field_key>managementnode.generated_uuid</field_key>
			<field_label>managementnode.generated_uuid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>a UUID created from the system hardware profile</field_description>
			<field_key>managementnode.local_uuid</field_key>
			<field_label>managementnode.local_uuid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 certificate of an authorized client that can use the system's CIM broker</field_description>
			<field_key>managementnode.ssl_client_certificate</field_key>
			<field_label>managementnode.ssl_client_certificate</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 private key of an authorized client that can use the system's CIM broker</field_description>
			<field_key>managementnode.ssl_client_key</field_key>
			<field_label>managementnode.ssl_client_key</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 public certificate of the system's CIM broker</field_description>
			<field_key>managementnode.ssl_server_certificate</field_key>
			<field_label>managementnode.ssl_server_certificate</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>zone_id</field_description>
			<field_key>managementnode.managing_zone.zone_id</field_key>
			<field_label>managementnode.managing_zone zone_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>managementnode.managing_zone.name</field_key>
			<field_label>managementnode.managing_zone.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>managementnode.managing_zone.description</field_key>
			<field_label>managementnode.managing_zone.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>created_date</field_description>
			<field_key>managementnode.managing_zone.created_date</field_key>
			<field_label>managementnode.managing_zone.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the port used by the system's CIM broker</field_description>
			<field_key>managementnode.agent_port</field_key>
			<field_label>managementnode.agent_port</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>state_change_date</field_description>
			<field_key>managementnode.state_change_date</field_key>
			<field_label>managementnode.state_change_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>credentials</field_description>
			<field_key>managementnode.credentials</field_key>
			<field_label>managementnode.credentials</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the database ID for the system type</field_description>
			<field_key>managementnode.system_type.system_type_id</field_key>
			<field_label>managementnode.system_type.system_type_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the name of the system type</field_description>
			<field_key>managementnode.system_type.name</field_key>
			<field_label>managementnode.system_type.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>inventory</options>
				<options>infrastructure-management-node</options>
				<options>infrastructure-windows-build-node</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>the description of the system type</field_description>
			<field_key>managementnode.system_type.description</field_key>
			<field_label>managementnode.system_type.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system type was added to inventory (UTC)</field_description>
			<field_key>managementnode.system_type.created_date</field_key>
			<field_label>managementnode.system_type.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>whether or not the system type is infrastructure</field_description>
			<field_key>managementnode.system_type.infrastructure</field_key>
			<field_label>managementnode.system_type.infrastructure</field_label>
			<value_type>bool</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the descriptor of available fields to create systems of this type</field_description>
			<field_key>managementnode.system_type.creation_descriptor</field_key>
			<field_label>managementnode.system_type.creation_descriptor</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>stage_id</field_description>
			<field_key>managementnode.stage.stage_id</field_key>
			<field_label>managementnode.stage.stage_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>managementnode.stage.name</field_key>
			<field_label>managementnode.stage.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>label</field_description>
			<field_key>managementnode.stage.label</field_key>
			<field_label>managementnode.stage.label</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>configuration</field_description>
			<field_key>managementnode.configuration</field_key>
			<field_label>managementnode.configuration</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>local</field_description>
			<field_key>managementnode.local</field_key>
			<field_label>managementnode.local</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>node_jid</field_description>
			<field_key>managementnode.node_jid</field_key>
			<field_label>managementnode.node_jid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>zone_id</field_description>
			<field_key>managing_zone.zone_id</field_key>
			<field_label>managing_zone.zone_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>managing_zone.name</field_key>
			<field_label>Management Zone</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>description</field_description>
			<field_key>managing_zone.description</field_key>
			<field_label>managing_zone.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>created_date</field_description>
			<field_key>managing_zone.created_date</field_key>
			<field_label>managing_zone.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system name</field_description>
			<field_key>name</field_key>
			<field_label>Name</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>network_id</field_description>
			<field_key>networks.network_id</field_key>
			<field_label>networks.network_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>created_date</field_description>
			<field_key>networks.created_date</field_key>
			<field_label>networks.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>ip_address</field_description>
			<field_key>networks.ip_address</field_key>
			<field_label>networks.ip_address</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>ipv6_address</field_description>
			<field_key>networks.ipv6_address</field_key>
			<field_label>networks.ipv6_address</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>device_name</field_description>
			<field_key>networks.device_name</field_key>
			<field_label>networks.device_name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>dns_name</field_description>
			<field_key>networks.dns_name</field_key>
			<field_label>networks.dns_name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>netmask</field_description>
			<field_key>networks.netmask</field_key>
			<field_label>networks.netmask</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>port_type</field_description>
			<field_key>networks.port_type</field_key>
			<field_label>networks.port_type</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>active</field_description>
			<field_key>networks.active</field_key>
			<field_label>networks.active</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>required</field_description>
			<field_key>networks.required</field_key>
			<field_label>networks.required</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system was registered in inventory (UTC)</field_description>
			<field_key>registration_date</field_key>
			<field_label>Registered</field_label>
			<basic_field>true</basic_field>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 certificate of an authorized client that can use the system's CIM broker</field_description>
			<field_key>ssl_client_certificate</field_key>
			<field_label>ssl_client_certificate</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 private key of an authorized client that can use the system's CIM broker</field_description>
			<field_key>ssl_client_key</field_key>
			<field_label>ssl_client_key</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>an x509 public certificate of the system's CIM broker</field_description>
			<field_key>ssl_server_certificate</field_key>
			<field_label>ssl_server_certificate</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>stage_id</field_description>
			<field_key>stage.stage_id</field_key>
			<field_label>stage.stage_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>name</field_description>
			<field_key>stage.name</field_key>
			<field_label>stage.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>label</field_description>
			<field_key>stage.label</field_key>
			<field_label>stage.label</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>state_change_date</field_description>
			<field_key>state_change_date</field_key>
			<field_label>Last State Changed</field_label>
			<basic_field>true</basic_field>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>system_event_id</field_description>
			<field_key>system_events.system_event_id</field_key>
			<field_label>system_events.system_event_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>time_created</field_description>
			<field_key>system_events.time_created</field_key>
			<field_label>system_events.time_created</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>time_enabled</field_description>
			<field_key>system_events.time_enabled</field_key>
			<field_label>system_events.time_enabled</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>priority</field_description>
			<field_key>system_events.priority</field_key>
			<field_label>system_events.priority</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>event_data</field_description>
			<field_key>system_events.event_data</field_key>
			<field_label>system_events.event_data</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the database ID for the system</field_description>
			<field_key>system_id</field_key>
			<field_label>System ID</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>system_log_id</field_description>
			<field_key>system_log.system_log_id</field_key>
			<field_label>system_log.system_log_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the database ID for the system type</field_description>
			<field_key>system_type.system_type_id</field_key>
			<field_label>system_type.system_type_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the name of the system type</field_description>
			<field_key>system_type.name</field_key>
			<field_label>system_type.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>inventory</options>
				<options>infrastructure-management-node</options>
				<options>infrastructure-windows-build-node</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>the description of the system type</field_description>
			<field_key>system_type.description</field_key>
			<field_label>system_type.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the date the system type was added to inventory (UTC)</field_description>
			<field_key>system_type.created_date</field_key>
			<field_label>system_type.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>whether or not the system type is infrastructure</field_description>
			<field_key>system_type.infrastructure</field_key>
			<field_label>rPath Infrastructure?</field_label>
			<basic_field>true</basic_field>
			<value_type>bool</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the descriptor of available fields to create systems of this type</field_description>
			<field_key>system_type.creation_descriptor</field_key>
			<field_label>system_type.creation_descriptor</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>system_job_id</field_description>
			<field_key>systemjob_set.system_job_id</field_key>
			<field_label>systemjob_set.system_job_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>event_uuid</field_description>
			<field_key>systemjob_set.event_uuid</field_key>
			<field_label>systemjob_set.event_uuid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>system_tag_id</field_description>
			<field_key>systemtag_set.system_tag_id</field_key>
			<field_label>systemtag_set.system_tag_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>query_tag_id</field_description>
			<field_key>systemtag_set.query_tag.query_tag_id</field_key>
			<field_label>systemtag_set.query_tag query_tag_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>The database id for the query set</field_description>
			<field_key>systemtag_set.query_tag.query_set.query_set_id</field_key>
			<field_label>systemtag_set.query_tag.query_set.query_set_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>Query set name</field_description>
			<field_key>systemtag_set.query_tag.query_set.name</field_key>
			<field_label>systemtag_set.query_tag.query_set.name</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>Query set description</field_description>
			<field_key>systemtag_set.query_tag.query_set.description</field_key>
			<field_label>systemtag_set.query_tag.query_set.description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>Date the query set was created</field_description>
			<field_key>systemtag_set.query_tag.query_set.created_date</field_key>
			<field_label>systemtag_set.query_tag.query_set.created_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>Date the query set was modified</field_description>
			<field_key>systemtag_set.query_tag.query_set.modified_date</field_key>
			<field_label>systemtag_set.query_tag.query_set.modified_date</field_label>
			<value_type>datetime</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>Name of the resource this query set operates on</field_description>
			<field_key>systemtag_set.query_tag.query_set.resource_type</field_key>
			<field_label>systemtag_set.query_tag.query_set.resource_type</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>query_tag</field_description>
			<field_key>systemtag_set.query_tag.query_tag</field_key>
			<field_label>systemtag_set.query_tag.query_tag</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>inclusion_method_id</field_description>
			<field_key>systemtag_set.inclusion_method.inclusion_method_id</field_key>
			<field_label>systemtag_set.inclusion_method.inclusion_method_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>inclusion_method</field_description>
			<field_key>systemtag_set.inclusion_method.inclusion_method</field_key>
			<field_label>systemtag_set.inclusion_method.inclusion_method</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options>
				<options>chosen</options>
				<options>filtered</options>
			</value_options>
		</field_descriptor>
		<field_descriptor>
			<field_description>targetid</field_description>
			<field_key>target.targetid</field_key>
			<field_label>target.targetid</field_label>
			<value_type>int</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targettype</field_description>
			<field_key>target.targettype</field_key>
			<field_label>target.targettype</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targetname</field_description>
			<field_key>target.targetname</field_key>
			<field_label>Target</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>id</field_description>
			<field_key>target_credentials.id</field_key>
			<field_label>target_credentials.id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>targetcredentialsid</field_description>
			<field_key>target_credentials.credentials.targetcredentialsid</field_key>
			<field_label>target_credentials.credentials.targetcredentialsid</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>credentials</field_description>
			<field_key>target_credentials.credentials.credentials</field_key>
			<field_label>target_credentials.credentials.credentials</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system description as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>target_system_description</field_key>
			<field_label>target_system_description</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system ID as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>target_system_id</field_key>
			<field_label>target_system_id</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system name as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>target_system_name</field_key>
			<field_label>System Name on Target</field_label>
			<basic_field>true</basic_field>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
		<field_descriptor>
			<field_description>the system state as reported by its target (only applies if system is on a virtual target)</field_description>
			<field_key>target_system_state</field_key>
			<field_label>target_system_state</field_label>
			<value_type>str</value_type>
			<operator_choices>
				<operator_choice>
					<key>NOT_IN</key>
					<label>not present in</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_LIKE</key>
					<label>does not contain</label>
				</operator_choice>
				<operator_choice>
					<key>LIKE</key>
					<label>contains</label>
				</operator_choice>
				<operator_choice>
					<key>EQUAL</key>
					<label>equal to</label>
				</operator_choice>
				<operator_choice>
					<key>NOT_EQUAL</key>
					<label>not equal to</label>
				</operator_choice>
				<operator_choice>
					<key>IN</key>
					<label>in</label>
				</operator_choice>
				<operator_choice>
					<key>IS_NULL</key>
					<label>is NULL</label>
				</operator_choice>
			</operator_choices>
			<value_options/>
		</field_descriptor>
	</field_descriptors>
</filter_descriptor>
"""
