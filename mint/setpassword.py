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
from mint import shimclient

from conary import dbstore

mintCfg = config.MintConfig()
mintCfg.read(config.RBUILDER_CONFIG)

db = dbstore.connect(mintCfg.dbPath, driver = mintCfg.dbDriver)
db.loadSchema()
cu = db.cursor()

username = ''
while not username:
    print "Username: ",
    username = sys.stdin.readline()[:-1]

    cu.execute('SELECT userId FROM Users WHERE username=?', username)
    res = cu.fetchone()
    if not res:
        username = ''
        print "No user by that name"
    else:
        userId = res[0]

passwd = ''
passwd2 = 'a'
while passwd != passwd2:
    passwd = getpass.getpass("Password: ")
    passwd2 = getpass.getpass("Again: ")
    if passwd != passwd2:
        print "Passwords don't match"

authToken = (mintCfg.authUser, mintCfg.authPass)
mintClient = shimclient.ShimMintClient(mintCfg, authToken)

user = mintClient.getUser(userId)
user.setPassword(passwd)
