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


import logging
import time
from conary.lib import digestlib
from M2Crypto import EVP
from M2Crypto import X509
from rmake.lib import gencert

from mint.rest.api.models import pki as pki_models
from mint.rest.db import manager

log = logging.getLogger(__name__)


KEY_LENGTH = 2048
# Expire after 10 years
EXPIRY = 3653


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

    def getCertificatePair(self, purpose):
        cu = self.db.cursor()
        cu.execute("""
            SELECT x509_pem, pkey_pem FROM pki_certificates
            WHERE purpose = ?
                AND time_issued < current_timestamp
                AND time_expired > current_timestamp
            ORDER BY time_expired DESC LIMIT 1
            """, purpose)
        res = cu.fetchone()
        if res is not None:
            return res[0], res[1]
        else:
            return None, None

    def getCACertificates(self):
        hg_ca = self.getCertificate(pki_models.PURPOSE_HGCA)
        lg_ca = self.getCertificate(pki_models.PURPOSE_LGCA)
        return hg_ca, lg_ca

    def createCertificate(self, purpose, desc, issuer=None, common=None):
        """Create and store one certificate.

        @param purpose: Machine-readable string identifying the purpose of this
                certificate.
        @param desc: Human-readable description to put into the certificate.
        @param issuer: Optional tuple C{(x509, pkey)} of issuer cert pair.
        @param common: Optional common name (hostname) for subject.
        """
        # Don't let anyone else even read the table while we work. We wouldn't
        # want two processes to read in the same CA serial index, generate
        # different certificates using the same serial, write them out to disk,
        # then blow up when they try to commit.
        cu = self.db.cursor()
        cu.execute("LOCK TABLE pki_certificates")

        subject = X509.X509_Name()
        subject.O = desc
        subject.OU = 'Created at ' + time.strftime('%F %T%z')
        if common is not None:
            subject.CN = common

        issuer_pkey = issuer_subject = issuer_fingerprint = serial = None
        if issuer is None:
            isCA = True
        else:
            isCA = False
            if isinstance(issuer, basestring):
                # Look up CA by purpose
                issuer_x509, issuer_pkey = self.getCertificatePair(issuer)
            else:
                # Tuple provided
                issuer_x509, issuer_pkey = issuer
            issuer_x509 = X509.load_cert_string(issuer_x509)
            issuer_pkey = EVP.load_key_string(issuer_pkey)
            issuer_subject = issuer_x509.get_subject()
            issuer_fingerprint = digestlib.sha1(
                    issuer_x509.as_der()).hexdigest()

            cu.execute("""UPDATE pki_certificates
                SET ca_serial_index = ca_serial_index + 1
                WHERE fingerprint = ?
                RETURNING ca_serial_index
                """, issuer_fingerprint)
            serial, = cu.fetchone()

        # Create certificates with a 'not before' date 1 day in the past, just
        # in case initial setup sets the clock backwards.
        rsa, x509 = gencert.new_cert(KEY_LENGTH, subject, EXPIRY,
                issuer=issuer_subject, issuer_evp=issuer_pkey, isCA=isCA,
                serial=serial, timestamp_offset=-86400)

        fingerprint = digestlib.sha1(x509.as_der()).hexdigest()
        pkey_pem = rsa.as_pem(None)
        x509_pem = x509.as_pem()

        cu.execute("""INSERT INTO pki_certificates (
                fingerprint, purpose, is_ca, x509_pem, pkey_pem,
                issuer_fingerprint, ca_serial_index, time_issued, time_expired
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            fingerprint, purpose, isCA, x509_pem, pkey_pem,
            issuer_fingerprint, 0,
            str(x509.get_not_before()), str(x509.get_not_after()),
            )

        log.info("Created certificate %s for purpose %r%s",
                fingerprint, purpose,
                (issuer_fingerprint and (" (issuer %s)" % issuer_fingerprint)
                    or ""))

        return x509_pem, pkey_pem
