#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

#LEVELS may only be appended at the end!  Numeric values are stored in the DB.  
#Any discrepency could result in a security issue.
NONMEMBER=-1
OWNER, DEVELOPER, USER = range(0, 3)

#This list is sorted in order of permissions
WRITERS = [OWNER, DEVELOPER]
READERS = [USER]
LEVELS = WRITERS + READERS


names = {
    OWNER:      "Owner",
    DEVELOPER:  "Developer",
    USER:       "User",
}

