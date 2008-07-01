# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import sys

from mint.buildtemplates import BooleanOption, IntegerOption, StringOption
from mint.config import isRBO

# this must be redefined in each template module due to sys.modules[__name__]
class Template(dict):
    def __init__(self):
        for option in self.__slots__:
            dict.__setitem__(self, option,
                             sys.modules[__name__].__dict__[option]())

# *** Extremely Important ***
# Changing the names or semantic meanings of option classes or templates is
# the same thing as making a schema upgrade! do not do this lightly.

###
# Option Classes
###

class newsletter(BooleanOption):
    default = False
    prompt = 'Would you like to receive the rPath Monthly Newsletter with rBuilder tips and tricks?'

class insider(BooleanOption):
    default = False
    prompt = "Would you like to participate in the \"rPath Insider's Group\" which reviews future releases and new build ideas?"

class searchResultsPerPage(IntegerOption):
    default = 10
    prompt = 'Number of search/browse entries to show per page'
    
class awsAccountNumber(StringOption):
    default = ''
    prompt = 'Account Number:'
    help = 'Please enter your Amazon Web Services account number as displayed on your AWS profile page.'
    
class awsPublicAccessKeyId(StringOption):
    default = ''
    prompt = 'Access Key ID:'
    help = 'Please enter your Amazon Web Services access key identifier as displayed on your AWS access identifiers page.'
    
class awsSecretAccessKey(StringOption):
    default = ''
    password = True
    prompt = 'Secret Access Key:'
    help = 'Please enter your Amazon Web Services secret access key as displayed on your AWS access identifiers page.'

###
# Templates
# classes must end with 'Template' to be properly processed.
###

class UserPrefsAttTemplate(Template):
    if isRBO():
        __slots__ = ['newsletter', 'insider']
    else:
        __slots__ = []

class UserPrefsNoAttTemplate(Template):
    __slots__ = ['searchResultsPerPage']

# Template for AWS settings
class UserPrefsAWSTemplate(Template):
    __slots__ = ['awsAccountNumber', 'awsPublicAccessKeyId', 'awsSecretAccessKey']

class UserPrefsInvisibleTemplate(Template):
    if isRBO():
        __slots__ = []
    else:
        __slots__ = ['newsletter', 'insider']

# Base template for items that should be displayed for user.
class UserPrefsVisibleTemplate(Template):
    __slots__ = UserPrefsAttTemplate.__slots__ + \
                UserPrefsNoAttTemplate.__slots__

# Base template for all legal data values.
class UserPrefsTemplate(Template):
    __slots__ = UserPrefsVisibleTemplate.__slots__ + \
                UserPrefsInvisibleTemplate.__slots__ + \
                UserPrefsAWSTemplate.__slots__

########################

for templateName in [x for x in sys.modules[__name__].__dict__.keys() \
                     if x.endswith('Template') and x != 'Template']:
    name = templateName[0].lower() + templateName[1:]
    sys.modules[__name__].__dict__[name] = \
             sys.modules[__name__].__dict__[templateName]()
