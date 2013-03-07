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

import base64
import hashlib
import hmac
import json
import os
import struct
import xmlrpclib
from conary.lib.util import AtomicFile
from Crypto.Cipher import AES
from Crypto.Util.strxor import strxor
from twisted.web import resource as tw_resource
from twisted.web import server as tw_server
from twisted.web import xmlrpc as tw_xmlrpc


class KeyWrapError(RuntimeError):
    pass


class AESStore(object):

    minlength = 256
    ckey_size = 32
    hkey_size = 128

    def __init__(self, keypath, init=False):
        if init and not os.path.exists(keypath):
            procs = 0
            with open('/proc/mounts', 'r') as fobj:
                for line in fobj:
                    line = line.split()
                    if len(line) > 2 and line[1] == '/proc':
                        procs += 1
            if procs != 1:
                raise RuntimeError("Cowardly refusing to generate keys while chrooted")
            with AtomicFile(keypath) as fobj:
                with open('/dev/random',  'rb') as devrandom:
                    fobj.write(devrandom.read(self.ckey_size + self.hkey_size))
        with open(keypath, 'rb') as fobj:
            self.key = fobj.read()

    @classmethod
    def _crypt(cls, nonce, ckey, data):
        """AES-256 in CTR mode"""
        stream = ''
        counter = 0
        assert len(ckey) == cls.ckey_size
        cipher = AES.new(ckey)
        while len(stream) < len(data):
            block = nonce + struct.pack('>Q', counter)
            stream += cipher.encrypt(block)
            counter += 1
        return strxor(stream[:len(data)], data)

    @classmethod
    def _hmac(cls, hkey, ciphertext):
        """SHA-512 HMAC"""
        assert len(hkey) == cls.hkey_size
        return hmac.new(hkey, ciphertext, hashlib.sha512).digest()

    @staticmethod
    def _dumps(data):
        """Compact JSON dump"""
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf8')

    def wrap(self, value, restrictions=None):
        """Wrap the given plaintext value and return a self-descriptive ciphertext"""
        metadata = {}
        if restrictions:
            metadata['r'] = restrictions
        # Pad plaintext to avoid divulging information about the plaintext's length
        plaintext = self._dumps(metadata) + '\0' + value
        plaintext += '\1'
        padding = self.minlength - len(plaintext) % self.minlength
        plaintext += '\0' * padding
        assert len(plaintext) % self.minlength == 0
        # Encrypt
        nonce = os.urandom(8)
        ckey = self.key[:self.ckey_size]
        ciphertext = self._crypt(nonce, ckey, plaintext)
        # Authenticate
        hkey = self.key[self.ckey_size:self.ckey_size+self.hkey_size]
        digest = self._hmac(hkey, ciphertext)
        blob = {'t': 'aes256',
                'n': base64.b64encode(nonce),
                'c': base64.b64encode(ciphertext),
                'h': base64.b64encode(digest),
                }
        return self._dumps(blob)

    def _unwrap(self, blob):
        """Internal unwrap function that doesn't enforce restrictions"""
        blob = json.loads(blob)
        # Authenticate
        hkey = self.key[self.ckey_size:self.ckey_size+self.hkey_size]
        ciphertext = base64.b64decode(blob['c'])
        digest = base64.b64decode(blob['h'])
        digest2 = self._hmac(hkey, ciphertext)
        if digest != digest2:
            raise KeyWrapError("hash check fail")
        # Decrypt
        ckey = self.key[:self.ckey_size]
        nonce = base64.b64decode(blob['n'])
        plaintext = self._crypt(nonce, ckey, ciphertext)
        # Unpad
        plaintext = plaintext.rstrip('\0')
        assert plaintext[-1] == '\1'
        plaintext = plaintext[:-1]
        # Extract metadata
        metadata, value = plaintext.split('\0', 1)
        metadata = json.loads(metadata)
        return metadata, value

    def unwrap(self, blob):
        """Unwrap the given ciphertext blob after checking if restrictions allow it"""
        metadata, value = self._unwrap(blob)
        if 'r' in metadata:
            raise KeyWrapError("unwrapping this credential is prohibited")
        return value


class CredServerRPC(tw_xmlrpc.XMLRPC):

    def __init__(self, stores):
        tw_xmlrpc.XMLRPC.__init__(self)
        self.stores = stores

    def xmlrpc_wrap(self, store, value, options):
        store = self.stores[store]
        restrictions = options.get('restrictions')
        try:
            return store.wrap(value, restrictions)
        except KeyWrapError, err:
            return xmlrpclib.Fault(str(err))

    def xmlrpc_unwrap(self, store, blob):
        store = self.stores[store]
        try:
            return store.unwrap(blob)
        except KeyWrapError, err:
            return xmlrpclib.Fault(err.__class__.__name__, str(err))


def CredServerFactory(keyDir, init=False):
    stores = {
            'default': AESStore(os.path.join(keyDir, 'aes256'), init=init),
            }
    rpc = CredServerRPC(stores)

    top = tw_resource.Resource()
    top.putChild('RPC2', rpc)
    return tw_server.Site(top)
