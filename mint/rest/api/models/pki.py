#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#


from mint.rest import modellib
from mint.rest.modellib import fields


PURPOSE_LGCA = 'lg_ca'
PURPOSE_HGCA = 'hg_ca'
PURPOSE_OUTBOUND = 'outbound'
PURPOSE_SITE = 'site'
PURPOSE_XMPP = 'xmpp'


class PKICertificate(modellib.Model):
    fingerprint = fields.CharField(isAttribute=True)
    purpose = fields.CharField()
    is_ca = fields.BooleanField()
    x509_pem = fields.CharField()
    pkey_pem = fields.CharField()
    issuer_fingerprint = fields.CharField()
    ca_serial_index = fields.IntegerField()
    time_issued = fields.CharField()
    time_expired = fields.CharField()
