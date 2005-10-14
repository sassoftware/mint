#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

WAITING, RUNNING, FINISHED, DELETED, ERROR, NOJOB = range(0, 6)

STATUSES = range(0, 6)
statusNames = {
    WAITING: "Waiting",
    RUNNING: "Running",
    FINISHED: "Finished",
    DELETED: "Deleted",
    ERROR: "Error",
    NOJOB: "No Job",
}
