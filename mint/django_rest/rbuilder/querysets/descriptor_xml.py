#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

system_query_set_descriptor_xml = """
<filter_descriptor>
    <field_descriptors>
        <field_descriptor>
            <field_label>Name</field_label>
            <field_key>name</field_key>
            <value_type>str</value_type>
            <value_options/>
            <operator_choices>
                <operator_choice>
                    <label>is</label>
                    <key>EQUAL</key>
                </operator_choice>
                <operator_choice>
                    <label>is not</label>
                    <key>NOT_EQUAL</key>
                </operator_choice>
                <operator_choice>
                    <label>matching</label>
                    <key>MATCHING</key>
                </operator_choice>
            </operator_choices>
        </field_descriptor>
        <field_descriptor>
            <field_label>current_state</field_label>
            <field_key>current_state</field_key>
            <value_type>str</value_type>
            <value_options>
                <option>Active</option>
                <option>Inactive</option>
            </value_options>
            <operator_choices>
                <operator_choice>
                    <label>is</label>
                    <key>EQUAL</key>
                </operator_choice>
                <operator_choice>
                    <label>is not</label>
                    <key>NOT_EQUAL</key>
                </operator_choice>
                <operator_choice>
                    <label>matching</label>
                    <key>MATCHING</key>
                </operator_choice>
            </operator_choices>
        </field_descriptor>
    </field_descriptors>
</filter_descriptor>
"""
