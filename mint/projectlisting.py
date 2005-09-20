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
    Projects.timeCreated, Projects.timeModified,
    count(projectUsers.userId) as devs 
        FROM
    Projects
        LEFT JOIN projectUsers ON
    Projects.projectId=projectUsers.projectId
        WHERE Projects.disabled=0 AND Projects.hidden=0
        GROUP BY Projects.projectId
        ORDER BY %s
        LIMIT %d
        OFFSET %d
"""

ordersql = {
    PROJECTNAME_ASC: "LOWER(Projects.name) ASC",
    PROJECTNAME_DES: "LOWER(Projects.name) DESC",
    LASTMODIFIED_ASC: "Projects.timeModified ASC",
    LASTMODIFIED_DES: "Projects.timeModified DESC",
    CREATED_ASC: "Projects.timeCreated ASC",
    CREATED_DES: "Projects.timeCreated DESC",
    NUMDEVELOPERS_ASC: "devs ASC",
    NUMDEVELOPERS_DES: "devs DESC",
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
