#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
