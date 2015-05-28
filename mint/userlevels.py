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


#LEVELS may only be appended at the end!  Numeric values are stored in the DB.  
#Any discrepency could result in a security issue.
(       NONMEMBER,  # not used in the db
        OWNER,
        DEVELOPER,
        USER,
        ADMIN,      # not used in the db (represents mintauth)
        )= range(-1, 4)

#This list is sorted in order of permissions
WRITERS = [OWNER, DEVELOPER]
READERS = [USER]
LEVELS = WRITERS + READERS


names = {
    OWNER:      "Owner",
    DEVELOPER:  "Developer",
    USER:       "User",
}

idsByName = dict((x[1].lower(), x[0]) for x in names.items())

def myProjectCompare(x, y):
    """This function is for use with displaying the user's projects in his My Projects
    pane.  Sort first by "level", and then by project name.
    """
    returner = int(x[1] - y[1])
    if not returner:
        return cmp(x[0].getName(), y[0].getName())
    return returner
