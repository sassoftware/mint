#!python

from conarycfg import ConfigFile
import urllib

class FixOwnersConfig(ConfigFile):
    defaults = {
        'privateUrlBase'        : 'http://%%s:%%s@mint.rpath.org/xmlrpc-private',
        'authUser'          : 'mintauth',
        'authPass'          : 'mintpass',
    }

    def read(self, path, exception = False):
        ConfigFile.read(self, path, exception)

        self.privateUrl = self.privateUrlBase%(urllib.quote(self.authUser), urllib.quote(self.authPass))
