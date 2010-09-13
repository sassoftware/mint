#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from mint.rest.api.models import pki as pki_models
from mint.rest.db import manager


class PKIManager(manager.Manager):

    def getCertificate(self, purpose):
        cu = self.db.cursor()
        cu.execute("""SELECT x509_pem FROM pki_certificates
            WHERE purpose = ?
                AND time_issued < current_timestamp
                AND time_expired > current_timestamp
            ORDER BY time_expired DESC LIMIT 1
            """, purpose)
        res = cu.fetchone()
        if res is not None:
            return res[0]
        else:
            return None

    def getCACertificates(self):
        hg_ca = self.getCertificate(pki_models.PURPOSE_HGCA)
        lg_ca = self.getCertificate(pki_models.PURPOSE_LGCA)
        return hg_ca, lg_ca
