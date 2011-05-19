#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import random
import time

from mint import helperfuncs
from mint.mint_error import *
from mint import usertemplates
from mint.db import users
from mint.lib import database

from conary.lib import sha1helper

# class User(database.TableObject):
#     __slots__ = [users.UsersTable.key] + users.UsersTable.fields
# 
#     def getItem(self, id):
#         return self.server.getUser(id)
# 
#     def getUsername(self):
#         return self.username
# 
#     def getFullName(self):
#         return self.fullName
# 
#     def getEmail(self):
#         return self.email
# 
#     def getDisplayEmail(self):
#         return self.displayEmail
# 
#     def getBlurb(self):
#         return self.blurb
# 
#     def setEmail(self, newEmail):
#         return self.server.setUserEmail(self.id, newEmail)
# 
#     def validateNewEmail(self, newEmail):
#         return self.server.validateNewEmail(self.id,newEmail)
# 
#     def setDisplayEmail(self, newEmail):
#         # NOTE: .strip done pre-insert for Kid's sake
#         return self.server.setUserDisplayEmail(self.id, newEmail.strip())
# 
#     def setPassword(self, newPassword):
#         self.server.setPassword(self.id, newPassword)
# 
#     def setBlurb(self, blurb):
#         # NOTE: .strip done pre-insert for Kid's sake
#         self.server.setUserBlurb(self.id, blurb.strip())
# 
#     def setFullName(self, fullName):
#         self.server.setUserFullName(self.id, fullName)
# 
#     def cancelUserAccount(self):
#         self.server.cancelUserAccount(self.id)
# 
#     def setDataValue(self, name, value):
#         self.server.setUserDataValue(self.username, name, value)
# 
#     def getDataValue(self, name):
#         return self.server.getUserDataValue(self.username, name)
# 
#     def getDefaultedData(self):
#         return self.server.getUserDataDefaulted(self.username)
# 
#     def getDataTemplate(self):
#         return usertemplates.userPrefsVisibleTemplate
#     
#     def getDefaultedDataAWS(self):
#         return self.server.getUserDataDefaultedAWS(self.username)
#     
#     def getDataTemplateAWS(self):
#         return usertemplates.userPrefsAWSTemplate
# 
#     def getDataDict(self, template = None):
#         dataDict = self.server.getUserDataDict(self.username)
#         if not template:
#             template = self.getDataTemplate()
#         for name in template:
#             if name not in dataDict:
#                 dataDict[name] = template[name][1]
#         return dataDict
# 
# 
# class Authorization(object):
#     """
#     Object describing a logged in user
#     @cvar authorized: True if this user is authorized with a good password, False if not.
#     @type authorized: bool
#     @cvar userId: database id of the user represented by this object
#     @type userId: int
#     @cvar username: username of the user
#     @type username: str
#     @cvar email: email address of the user
#     @type email: str
#     @cvar displayEmail: email address of user provided for public display
#     @type displayEmail: str
#     @cvar fullName: full name of the user
#     @type fullName: str
#     @cvar blurb: a short description about and written by the user
#     @type blurb: str
#     @cvar timeAccessed: The time that the user last logged in
#     @type timeAccessed: float
#     @cvar groups: a list dictionaries containing the groups to which the user belongs
#     @type groups: list
#     """
#     __slots__ = ('authorized', 'userId', 'username', 'email',
#                  'displayEmail', 'fullName', 'blurb', 'token', 'stagnant',
#                  'groups', 'admin', 'timeAccessed')
# 
#     def __init__(self, **kwargs):
#         for key in self.__slots__:
#             if key in kwargs:
#                 self.__setattr__(key, kwargs[key])
#             else:
#                 self.__setattr__(key, None)
# 
#     def setToken(self, authToken):
#         self.token = authToken
# 
#     def getToken(self):
#         return self.token
# 
#     def getDict(self):
#         d = {}
#         for slot in self.__slots__:
#             d[slot] = self.__getattribute__(slot)
#         return d
# 
# def confirmString():
#     """
#     Generate a confirmation string
#     """
#     hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
#     return sha1helper.sha1ToString(hash)
# 
# 
# def newPassword(length = 6):
#     """
#     @param length: length of random password generated
#     @returns: returns a character string of random letters and digits.
#     @rtype: str
#     """
#     return helperfuncs.genPassword(length)



class User(database.TableObject):
    __slots__ = [users.UsersTable.key] + users.UsersTable.fields

    def getItem(self, id):
        return self.server.getUser(id)

    def getUsername(self):
        return self.user_name

    def getFullName(self):
        return self.full_name

    def getEmail(self):
        return self.email

    def getDisplayEmail(self):
        return self.display_email

    def getBlurb(self):
        return self.blurb

    def setEmail(self, newEmail):
        return self.server.setUserEmail(self.id, newEmail)

    def validateNewEmail(self, newEmail):
        return self.server.validateNewEmail(self.id,newEmail)

    def setDisplayEmail(self, newEmail):
        # NOTE: .strip done pre-insert for Kid's sake
        return self.server.setUserDisplayEmail(self.id, newEmail.strip())

    def setPassword(self, newPassword):
        self.server.setPassword(self.id, newPassword)

    def setBlurb(self, blurb):
        # NOTE: .strip done pre-insert for Kid's sake
        self.server.setUserBlurb(self.id, blurb.strip())

    def setFullName(self, fullName):
        self.server.setUserFullName(self.id, fullName)

    def cancelUserAccount(self):
        self.server.cancelUserAccount(self.id)

    def setDataValue(self, name, value):
        self.server.setUserDataValue(self.user_name, name, value)

    def getDataValue(self, name):
        return self.server.getUserDataValue(self.user_name, name)

    def getDefaultedData(self):
        return self.server.getUserDataDefaulted(self.user_name)

    def getDataTemplate(self):
        return usertemplates.userPrefsVisibleTemplate
    
    def getDefaultedDataAWS(self):
        return self.server.getUserDataDefaultedAWS(self.user_name)
    
    def getDataTemplateAWS(self):
        return usertemplates.userPrefsAWSTemplate

    def getDataDict(self, template = None):
        dataDict = self.server.getUserDataDict(self.user_name)
        if not template:
            template = self.getDataTemplate()
        for name in template:
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict


class Authorization(object):
    """
    Object describing a logged in user
    @cvar authorized: True if this user is authorized with a good password, False if not.
    @type authorized: bool
    @cvar userId: database id of the user represented by this object
    @type userId: int
    @cvar username: username of the user
    @type username: str
    @cvar email: email address of the user
    @type email: str
    @cvar displayEmail: email address of user provided for public display
    @type displayEmail: str
    @cvar fullName: full name of the user
    @type fullName: str
    @cvar blurb: a short description about and written by the user
    @type blurb: str
    @cvar timeAccessed: The time that the user last logged in
    @type timeAccessed: float
    @cvar groups: a list dictionaries containing the groups to which the user belongs
    @type groups: list
    """
    __slots__ = ('authorized', 'userId', 'username', 'email',
                 'displayEmail', 'fullName', 'blurb', 'token', 'stagnant',
                 'groups', 'admin', 'timeAccessed')

    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key in kwargs:
                self.__setattr__(key, kwargs[key])
            else:
                self.__setattr__(key, None)

    def setToken(self, authToken):
        self.token = authToken

    def getToken(self):
        return self.token

    def getDict(self):
        d = {}
        for slot in self.__slots__:
            d[slot] = self.__getattribute__(slot)
        return d

def confirmString():
    """
    Generate a confirmation string
    """
    hash = sha1helper.sha1String(str(random.random()) + str(time.time()))
    return sha1helper.sha1ToString(hash)


def newPassword(length = 6):
    """
    @param length: length of random password generated
    @returns: returns a character string of random letters and digits.
    @rtype: str
    """
    return helperfuncs.genPassword(length)
