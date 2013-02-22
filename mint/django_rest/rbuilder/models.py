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

from django.db import models

from mint.django_rest.rbuilder import modellib

XObjHidden = modellib.XObjHidden


class Fault(modellib.XObjModel):
    class Meta:
        abstract = True
    code = models.IntegerField(null=True)
    message = models.CharField(max_length=8092, null=True)
    traceback = models.TextField(null=True)

class DatabaseVersion(modellib.XObjModel):
    class Meta:
        db_table = u'databaseversion'
    version = models.SmallIntegerField(null=True)
    minor = models.SmallIntegerField(null=True)


class Pk(object):
    def __init__(self, pk):
        self.pk = pk


class PkiCertificates(modellib.XObjModel):
    class Meta:
        db_table = 'pki_certificates'
        unique_together = [ ('fingerprint', 'ca_serial_index') ]
    fingerprint = models.TextField(primary_key=True)
    purpose = models.TextField(null=False)
    is_ca = models.BooleanField(null=False, default=False)
    x509_pem = models.TextField(null=False)
    pkey_pem = models.TextField(null=False)
    issuer_fingerprint = models.ForeignKey('self',
        db_column="issuer_fingerprint", null=True)
    ca_serial_index = models.IntegerField(null=True)
    time_issued = modellib.DateTimeUtcField(null=False)
    time_expired = modellib.DateTimeUtcField(null=False)

class Jobs(modellib.XObjModel):
    class Meta:
        db_table = 'jobs'
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.TextField(max_length=64, null=False)
