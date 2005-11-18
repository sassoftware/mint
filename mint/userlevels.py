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

def myProjectCompare(x, y):
    """This function is for use with displaying the user's projects in his My Projects
    pane.  Sort first by "level", and then by project name.
    """
    returner = int(x[1] - y[1])
    if not returner:
        return cmp(x[0].getName(), y[0].getName())
    return returner
