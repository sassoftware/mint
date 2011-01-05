#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

queryset_post_xml = """\
<query_set>
    <name>Unmanaged systems</name>
    <resource_type>system</resource_type>
    <filter_entries>
        <filter_entry field="current_state.name" operator="EQUAL" value="unmanaged"/>
    </filter_entries>
</query_set>
"""
