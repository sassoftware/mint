#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

(
    PROJECTNAME_ASC,
    PROJECTNAME_DES,
    LASTMODIFIED_ASC,
    LASTMODIFIED_DES,
    CREATED_ASC,
    CREATED_DES,
    NUMDEVELOPERS_ASC,
    NUMDEVELOPERS_DES ) = range(0, 8)

descindex = 2
desctrunclength = 300

# FIXME sqlbase has been badly mangled due to sqlite3 not handling "group by" and "order by" combined with joins in any semblance of a sane fashion. the code below is a workaround. original sqlbase is included in comments. note that group by and having alteration should probably be worked into original code. it's faster.

#sqlbase = """SELECT Projects.hostname, Projects.name, Projects.desc,
#    IFNULL(MAX(Commits.timestamp), Projects.timeCreated) AS timeModified
#        FROM
#    Projects
#        LEFT JOIN Commits ON
#    Projects.projectId=Commits.projectId
#        WHERE Projects.disabled=0 AND Projects.hidden=0
#        GROUP BY Projects.projectId
#        ORDER BY %s
#        LIMIT %d
#        OFFSET %d
#"""


sqlbase = """ SELECT hostname, name, desc, timeModified FROM
        (SELECT projects.projectId as projectId, Projects.hostname as hostname, Projects.name as name, Projects.desc as desc,
    IFNULL(MAX(Commits.timestamp), Projects.timeCreated) AS timeModified
        FROM
    Projects
        LEFT JOIN Commits ON
    Projects.projectId=Commits.projectId
        GROUP BY Projects.projectId
        HAVING Projects.disabled=0 AND Projects.hidden=0)
        ORDER BY %s
        LIMIT %d
        OFFSET %d
"""

# FIXME NUM_DEVS_STRING has been modified to match new sqlbase
NUM_DEVS_STRING = "(SELECT count(*) FROM ProjectUsers WHERE ProjectUsers.projectId=projectId)"

# FIXME. NUMDEVELOPERS needs to go away and be replaced by a true popularity metric. Note the effect on "browse projects box"--most popular projects.
ordersql = {
    PROJECTNAME_ASC: "LOWER(name) ASC",
    PROJECTNAME_DES: "LOWER(name) DESC",
    LASTMODIFIED_ASC: "timeModified ASC",
    LASTMODIFIED_DES: "timeModified DESC",
#    CREATED_ASC: "Projects.timeCreated ASC",
#    CREATED_DES: "Projects.timeCreated DESC",
    NUMDEVELOPERS_ASC: NUM_DEVS_STRING+" ASC",
    NUMDEVELOPERS_DES: NUM_DEVS_STRING+" DESC",
}

orderhtml = {
    PROJECTNAME_ASC: "Project name in ascending order",
    PROJECTNAME_DES: "Project name in descending order",
    LASTMODIFIED_ASC: "Least recently modified",
    LASTMODIFIED_DES: "Most recently modified",
#    CREATED_ASC:      "Oldest",
#    CREATED_DES:      "Newest",
    NUMDEVELOPERS_ASC: "Fewest developers",
    NUMDEVELOPERS_DES: "Most developers",
}
