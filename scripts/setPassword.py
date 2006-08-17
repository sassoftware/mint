#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import sys, os
import md5
import getpass

from mint import config
from mint.client import MintClient

from conary import dbstore

mintCfg = config.MintConfig()
mintCfg.read(config.RBUILDER_CONFIG)

db = dbstore.connect(mintCfg.dbPath, driver = mintCfg.dbDriver)
db.loadSchema()
cu = db.cursor()

print "Username: ",
username = sys.stdin.readline()[:-1]

passwd = getpass.getpass("Passphrase: ")

m = md5.new()
salt = os.urandom(4)
m.update(salt)
m.update(passwd)
hash = m.hexdigest()

cu.execute("UPDATE Users SET salt=?, passwd=? WHERE username=?",
           salt, hash, username)
db.commit()
