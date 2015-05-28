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


import os
import unittest
from testutils import mock
from StringIO import StringIO as _StringIO

from mint.scripts import cred_server


class StringIO(_StringIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


class CredStoreTest(unittest.TestCase):

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        mock.unmockAll()

    def testAES(self):
        keyfile = StringIO('\0' * 160)
        mock.mock(cred_server, 'open')
        cred_server.open._mock.appendReturn(keyfile, 'keyfile', 'rb')
        mock.mock(os, 'urandom')
        os.urandom._mock.appendReturn('\0' * 8, 8)
        store = cred_server.AESStore('keyfile')

        one = store.wrap('one')
        self.assertEqual(one, vector1)
        self.assertEqual(store.unwrap(one), 'one')
        two = store.wrap('two', restrictions='kerberos')
        self.assertEqual(two, vector2)
        self.assertRaises(cred_server.KeyWrapError, store.unwrap, two)
        self.assertEqual(store._unwrap(two), ({'r': 'kerberos'}, 'two'))


vector1 = '{"c":"p+jAF8wliImtSKIUkoQgh1MPivvHRTa5qWO08cTLc4vOp0A9TWBrbgdOxdO6850YcmADyjemKnTRovWOdQY1jt1KsShNSuF7QehZJEcMNvdHQcvhgbt/MGF8HeOrDDof0MSPcyGoLTdglazgQZFnoLyvSbDAzqYt5rwcZlReHa2r+nfNboXaJF+wvcXlLPwpugrhqyg34PNjh7cOkxdgEkNiwrtm2PSxN/zoNCyc04ahFEKW4nJoqOUN9TeoBdV5uyHrvfNX7TS/WLWDcVDdyvNiIl5iCmBwrF71KftSJGZ2i3jAS1TlHvX6B+UGo1/GsLcQJJyGJuGpatV4KNe+Lg==","h":"tbrKH7YAqB5n1jhkxIk0uXf0VvdRGTeffE8t0wFKEvyc85t8NDE3wcdlkS1S5TyfGFR+irTmCEQh/+KxkQ6bzQ==","n":"AAAAAAAAAAA=","t":"aes256"}'
vector2 = '{"c":"p7eyWphi4uzfKsdm/fcC+lN7/ZTGRTa5qWO08cTLc4vOp0A9TWBrbgdOxdO6850YcmADyjemKnTRovWOdQY1jt1KsShNSuF7QehZJEcMNvdHQcvhgbt/MGF8HeOrDDof0MSPcyGoLTdglazgQZFnoLyvSbDAzqYt5rwcZlReHa2r+nfNboXaJF+wvcXlLPwpugrhqyg34PNjh7cOkxdgEkNiwrtm2PSxN/zoNCyc04ahFEKW4nJoqOUN9TeoBdV5uyHrvfNX7TS/WLWDcVDdyvNiIl5iCmBwrF71KftSJGZ2i3jAS1TlHvX6B+UGo1/GsLcQJJyGJuGpatV4KNe+Lg==","h":"eLz/r1/sDSToJfkoyyWmObM8InmnIoQo8FhaduR+4Og2b9dfwd3xQpJk1F83ZN1iZ/LIzhU3/XumCP/PxXN/+w==","n":"AAAAAAAAAAA=","t":"aes256"}'
