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
sqlbase = """SELECT Projects.hostname, Projects.name, Projects.desc,
    IFNULL(MAX(Commits.timestamp), Projects.timeCreated) AS timeModified
        FROM
    Projects
        LEFT JOIN Commits ON
    Projects.projectId=Commits.projectId
        WHERE Projects.disabled=0 AND Projects.hidden=0
        GROUP BY Projects.projectId
        ORDER BY %s
        LIMIT %d
        OFFSET %d
"""

NUM_DEVS_STRING = "(SELECT count(*) FROM ProjectUsers WHERE ProjectUsers.projectId=Projects.projectId)"

# FIXME. NUMDEVELOPERS needs to go away and be replaced by a true popularity metric. Note the effect on "browse projects box"--most popular projects.
ordersql = {
    PROJECTNAME_ASC: "LOWER(Projects.name) ASC",
    PROJECTNAME_DES: "LOWER(Projects.name) DESC",
    LASTMODIFIED_ASC: "timeModified ASC",
    LASTMODIFIED_DES: "timeModified DESC",
    CREATED_ASC: "Projects.timeCreated ASC",
    CREATED_DES: "Projects.timeCreated DESC",
    NUMDEVELOPERS_ASC: NUM_DEVS_STRING+" ASC",
    NUMDEVELOPERS_DES: NUM_DEVS_STRING+" DESC",
}

orderhtml = {
    PROJECTNAME_ASC: "Project name in ascending order",
    PROJECTNAME_DES: "Project name in descending order",
    LASTMODIFIED_ASC: "Least recently modified",
    LASTMODIFIED_DES: "Most recently modified",
    CREATED_ASC:      "Oldest",
    CREATED_DES:      "Newest",
    NUMDEVELOPERS_ASC: "Fewest developers",
    NUMDEVELOPERS_DES: "Most developers",
}
