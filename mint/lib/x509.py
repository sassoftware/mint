#
# Copyright (c) 2008-2010 rPath, Inc.  All Rights Reserved.
#
"Simple module for generating x509 certificates"

from conary.lib import digestlib
from rmake.lib import gencert

class X509(object):
    class Subject(gencert.X509.X509_Name):
        __slots__ = ['C', 'ST', 'L', 'O', 'OU', 'CN', 'emailAddress']
        def __init__(self, **kwargs):
            gencert.X509.X509_Name.__init__(self)
            for slot in self.__slots__:
                val = kwargs.get(slot, None)
                if val is not None:
                    setattr(self, slot, val)

    KEY_LENGTH = 2048
    # Expire after 10 years
    EXPIRY = 3653
    TIMESTAMP_OFFSET = 0

    def __init__(self, x509, pkey):
        self.x509 = x509
        self.pkey = pkey

    @classmethod
    def new(cls, subject=None, keyLength=None, serial=None, expiry=None,
            timestampOffset=None, issuer_x509=None, issuer_pkey=None,
            isCA=False):
        keyLength = (keyLength is not None and keyLength) or cls.KEY_LENGTH
        expiry = (expiry is not None and expiry) or cls.EXPIRY
        timestampOffset = (timestampOffset is not None and timestampOffset) \
            or cls.TIMESTAMP_OFFSET

        if subject is None:
            subject = cls.Subject(CN="Test Certificate")

        issuer_subject = None
        if issuer_x509 is not None:
            issuer_subject = issuer_x509.get_subject()

        rsa, x509 = gencert.new_cert(keyLength, subject, expiry,
                issuer=issuer_subject, issuer_evp=issuer_pkey, isCA=isCA,
                serial=serial, timestamp_offset=timestampOffset)

        return cls(x509, rsa)

    def load_x509_file(self, certFile):
        self.x509 = gencert.X509.load_cert(certFile)

    def load_x509(self, pem):
        self.x509 = gencert.X509.load_cert_string(pem.encode('ascii'))

    def load_pkey_file(self, keyFile, callback=None):
        kwargs = {}
        if callback is not None:
            kwargs['callback'] = callback
        self.pkey = gencert.EVP.load_key(keyFile, **kwargs)

    def load_pkey(self, pem, callback=None):
        kwargs = {}
        if callback is not None:
            kwargs['callback'] = callback
        self.pkey = gencert.EVP.load_key_string(pem.encode('ascii'), **kwargs)

    def load_from_strings(self, pemX509, pemPkey=None, callback=None):
        self.load_x509(pemX509)
        if pemPkey:
            self.load_pkey(pemPkey, callback=callback)

    @property
    def hash_issuer(self):
        certHash = "%08x" % self.x509.get_issuer().as_hash()
        return certHash

    @property
    def hash(self):
        certHash = "%08x" % self.x509.get_subject().as_hash()
        return certHash

    @property
    def fingerprint(self):
        return digestlib.sha1(self.x509.as_der()).hexdigest()
