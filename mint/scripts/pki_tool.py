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


"""
Manipulate certificates in the rBuilder database.
"""

import grp
import logging
import optparse
import os
import psycopg2
import socket
import time
from conary.lib import digestlib
from conary.lib import util as cny_util
from M2Crypto import EVP
from M2Crypto import X509
from rmake.lib import gencert

from mint import config
from mint.lib.scriptlibrary import GenericScript

log = logging.getLogger(__name__)

KEY_LENGTH = 2048
# Expire after 10 years
EXPIRY = 3653

DEPLOY_LIST = [
        ('site', '/srv/rbuilder/pki/httpd.pem', 'apache'),
        ('site', '/srv/rbuilder/pki/rmake.pem', 'rmake'),
        ('xmpp', '/srv/rbuilder/pki/jabberd.pem', 'jabber'),
        ('outbound', '/srv/rbuilder/pki/outbound.pem', 'root'),
        # Don't rely on these files, they are just for debugging.
        ('lg_ca', '/srv/rbuilder/pki/lg_ca.crt', 'root'),
        ('hg_ca', '/srv/rbuilder/pki/hg_ca.crt', 'root'),
        ]


class Script(GenericScript):
    logFileName = 'scripts.log'
    newLogger = True

    def action(self):
        parser = optparse.OptionParser()
        parser.add_option('-c', '--config-file',
                default=config.RBUILDER_CONFIG)
        parser.add_option('-q', '--quiet', action='store_true')
        parser.add_option('-v', '--verbose', action='store_true')
        parser.add_option('-n', '--dry-run', action='store_true')

        parser.add_option('-i', '--initialize', action='store_true',
                help="Create or refresh initial set of certificates.")
        parser.add_option('-d', '--deploy', action='store_true',
                help="Re-deploy existing certificates")

        options, args = parser.parse_args()
        if args:
            parser.error("No arguments expected.")

        self.loadConfig(options.config_file)
        self.resetLogging(quiet=options.quiet, verbose=options.verbose)
        self.dry_run = options.dry_run
        self.db = psycopg2.connect(**self.cfg.getDBParams())

        # Don't let anyone else even read the table while we work. We wouldn't
        # want two processes to read in the same CA serial index, generate
        # different certificates using the same serial, write them out to disk,
        # then blow up when they try to commit.
        cu = self.db.cursor()
        cu.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cu.execute("LOCK TABLE pki_certificates")

        if options.initialize:
            self.initialize()
        elif options.deploy:
            self.deploy()
        else:
            parser.error("Expected --initialize or --deploy")

    def _fetch(self):
        """List all active certificates, keeping only the most distantly
        expiring for each purpose."""
        cu = self.db.cursor()
        cu.execute("""
            SELECT DISTINCT ON ( purpose ) purpose, x509_pem, pkey_pem
            FROM pki_certificates
            WHERE time_issued < current_timestamp
                AND time_expired > current_timestamp
                ORDER BY purpose, time_expired DESC
            """)
        return cu

    def initialize(self):
        """Create and deploy all missing certificates."""

        certs = dict((x[0], x[1:]) for x in self._fetch())

        # Create, insert and deploy missing certificates
        fqdn = socket.gethostname()
        # CAs have no CN because they're never utilized directly.
        self._create(certs, 'hg_ca',
                desc="rBuilder High-Grade Certificate Authority")
        self._create(certs, 'lg_ca',
                desc="rBuilder Low-Grade Certificate Authority")
        # The site certificate has a CN. After changing the system hostname, it
        # may need to be regenerated.
        self._create(certs, 'site', issuer=certs['hg_ca'],
                desc='rBuilder Site Certificate', common=fqdn)
        # These have no CN because they're not public services and aren't
        # necessarily accessed via a "well-known" name.
        self._create(certs, 'xmpp', issuer=certs['hg_ca'],
                desc='rBuilder XMPP Certificate')
        # This is used for CIM connections outbound from the local system.
        self._create(certs, 'outbound', issuer=certs['lg_ca'],
                desc='rBuilder Repeater Client Certificate')

        if self.dry_run:
            log.info("Dry run finished; rolling back.")
            self.db.rollback()
        else:
            self.db.commit()
            self.deploy()

    def _create(self, certs, purpose, desc, issuer=None, common=None):
        """Create and store one certificate."""
        if purpose in certs:
            return
        cu = self.db.cursor()

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
            issuer_x509 = X509.load_cert_string(issuer[0])
            issuer_pkey = EVP.load_key_string(issuer[1])
            issuer_subject = issuer_x509.get_subject()
            issuer_fingerprint = digestlib.sha1(
                    issuer_x509.as_der()).hexdigest()

            cu.execute("""UPDATE pki_certificates
                SET ca_serial_index = ca_serial_index + 1
                WHERE fingerprint = %s
                RETURNING ca_serial_index
                """, (issuer_fingerprint,))
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (fingerprint, purpose, isCA, x509_pem, pkey_pem,
                issuer_fingerprint, 0,
                str(x509.get_not_before()), str(x509.get_not_after()),
                ))

        log.info("Created certificate %s for purpose %r%s%s",
                fingerprint, purpose,
                (issuer_fingerprint and (" (issuer %s)" % issuer_fingerprint)
                    or ""),
                self.dry_run and " (dry run)" or "")

        certs[purpose] = x509_pem, pkey_pem

    def deploy(self):
        """Write all certificates out to the filesystem."""
        for purpose, x509, pkey in self._fetch():
            for d_purpose, path, group in DEPLOY_LIST:
                if d_purpose != purpose:
                    continue
                self._deploy(purpose, x509, pkey, path, group)

    def _deploy(self, purpose, x509, pkey, path, group):
        """Write one certificate to the filesystem."""
        try:
            groupid = grp.getgrnam(group).gr_gid
        except KeyError:
            log.info("Not deploying %r to %s: group %s not found.",
                    purpose, path, group)
            return

        fobj = cny_util.AtomicFile(path, chmod=0640)
        os.chown(fobj.name, 0, groupid)

        ext = path.split('.')[-1]
        assert ext in ('pem', 'crt', 'key')
        if ext in ('pem', 'crt'):
            fobj.write(x509)
        if ext in ('pem', 'key'):
            fobj.write(pkey)

        if self.dry_run:
            fobj.close()
            log.debug("Would deploy %r to %s (group %s)", purpose, path, group)
        else:
            fobj.commit()
            log.debug("Deployed %r to %s (group %s)", purpose, path, group)
