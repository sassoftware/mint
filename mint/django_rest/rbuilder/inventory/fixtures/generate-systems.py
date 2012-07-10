#!/usr/bin/python

SYSTEM_TEMPLATE = """
    <object pk="%(systemId)s" model="inventory.system">
        <field type="CharField" name="name">System name %(systemId)s</field>
        <field type="CharField" name="description">System description %(systemId)s</field>
        <field type="DateTimeField" name="created_date">2010-12-06 22:11:00</field>
        <field type="DateTimeField" name="launch_date"><None></None></field>
        <field to="rbuilder.targets" name="target" rel="ManyToOneRel"><None></None></field>
        <field type="CharField" name="target_system_id"><None></None></field>
        <field type="DateTimeField" name="registration_date"><None></None></field>
        <field type="CharField" name="generated_uuid">system-%(systemId)s-generated-uuid</field>
        <field type="CharField" name="local_uuid">system-%(systemId)s-local-uuid</field>
        <field type="CharField" name="_ssl_client_certificate">system-%(systemId)s-ssl-client-certificate</field>
        <field type="CharField" name="_ssl_client_key">system-%(systemId)s-ssl-client-key</field>
        <field type="CharField" name="ssl_server_certificate">system-%(systemId)s-ssl-server-certificate</field>
        <field to="users.users" name="launching_user" rel="ManyToOneRel"><None></None></field>
        <field to="inventory.systemstate" name="current_state" rel="ManyToOneRel">1</field>
        <field to="inventory.zone" name="managing_zone" rel="ManyToOneRel">1</field>
        <field to="inventory.systemtype" name="system_type" rel="ManyToOneRel">1</field>
    </object>

   <object pk="%(systemId)s" model="inventory.network">
        <field to="inventory.system" name="system" rel="ManyToOneRel">%(systemId)s</field>
        <field type="CharField" name="ip_address"><None></None></field>
        <field type="CharField" name="ipv6_address"><None></None></field>
        <field type="CharField" name="device_name"></field>
        <field type="CharField" name="dns_name">127.0.0.%(systemId)s</field>
        <field type="CharField" name="netmask"><None></None></field>
        <field type="CharField" name="port_type"><None></None></field>
        <field type="NullBooleanField" name="active"><None></None></field>
        <field type="NullBooleanField" name="required"><None></None></field>
        <field type="DateTimeField" name="created_date">2010-10-05 18:36:37</field>
  </object>"""


f = open('system_collection.xml', 'w')
f.write("""<?xml version="1.0" encoding="utf-8"?>""")
f.write("""<django-objects version="1.0">""")

for i in range(200):
    # Start at 3 since we already have other fixtures that might be loaded
    # that create systems 0-2.
    f.write(SYSTEM_TEMPLATE % {"systemId":i+3})

f.write("""</django-objects>""")
f.close()

