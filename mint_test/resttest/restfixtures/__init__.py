import sys

from mint_test import fixtures

class _RestFixture(object):
    def __init__(self, test):
        self.test = test

    def load(self, mintCfg):
        self.test.mintCfg = mintCfg
        self._load()
        return mintCfg, {}

    def __getattr__(self, key):
        return getattr(self.test, key)

    def _load(self):
        raise NotImplementedError

class EmptyFixture(_RestFixture):
    name = 'empty'
    def _load(self):
        self.createUser('admin', admin=True)


fixtures = {}
for val in sys.modules[__name__].__dict__.values():
    if (val != _RestFixture and isinstance(val, type) 
            and issubclass(val, _RestFixture)):
        fixtures[val.name] = val
