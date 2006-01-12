#
# Copyright (c) 2005-2006 rPath, Inc.
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
    NUMDEVELOPERS_DES,
    ACTIVITY_ASC,
    ACTIVITY_DES) = range(0, 10)

descindex = 2
desctrunclength = 300

# FIXME sqlbase has been badly mangled due to sqlite3 not handling "group by" and "order by" combined with joins in any semblance of a sane fashion. the code below is a workaround. original sqlbase is included in comments. note that group by and having alteration should probably be worked into original code. it's faster.

#sqlbase = """SELECT Projects.projectId, Projects.hostname, Projects.name, Projects.description,
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

sqlbase = """        
    SELECT projectId, hostname, name, description, timeModified
        FROM (SELECT Projects.projectId AS projectId,
                     Projects.hostname AS hostname,
                     Projects.name AS name,
                     Projects.description AS description,
                     Projects.projectId NOT IN (select DISTINCT projectId FROM Commits) AS fledgeling,
                     IFNULL(MAX(Commits.timestamp), Projects.timeCreated) AS timeModified,
                     (SELECT count(*) FROM Commits WHERE Commits.projectId=Projects.projectId AND Commits.timestamp > (SELECT IFNULL(MAX(timestamp)-604800, 0) FROM Commits)) AS recentCommits,
                     timeCreated,
                     (SELECT COUNT(userId) AS numDevs FROM ProjectUsers WHERE ProjectUsers.projectId=Projects.projectId) AS numDevs
                     FROM
                         Projects
                     LEFT JOIN Commits ON
                     Projects.projectId=Commits.projectId AND Projects.disabled=0 AND Projects.hidden=0
                     GROUP BY Projects.projectId) as P
    WHERE fledgeling = 0
    ORDER BY %s
    LIMIT %d
    OFFSET %d
"""

ordersql = {
    PROJECTNAME_ASC:   "LOWER(name) ASC",
    PROJECTNAME_DES:   "LOWER(name) DESC",
    LASTMODIFIED_ASC:  "timeModified ASC",
    LASTMODIFIED_DES:  "timeModified DESC",
    CREATED_ASC:       "timeCreated ASC",
    CREATED_DES:       "timeCreated DESC",
    NUMDEVELOPERS_ASC: "numDevs ASC",
    NUMDEVELOPERS_DES: "numDevs DESC",
    ACTIVITY_ASC:      "recentCommits ASC, timeModified ASC",
    ACTIVITY_DES:      "recentCommits DESC, timeModified DESC",
}

orderhtml = {
    PROJECTNAME_ASC:   "Project name in ascending order",
    PROJECTNAME_DES:   "Project name in descending order",
    LASTMODIFIED_ASC:  "Least recently modified",
    LASTMODIFIED_DES:  "Most recently modified",
    CREATED_ASC:       "Oldest",
    CREATED_DES:       "Newest",
    NUMDEVELOPERS_ASC: "Least Popular",
    NUMDEVELOPERS_DES: "Most Popular",
    ACTIVITY_ASC:      "Least Active",
    ACTIVITY_DES:      "Most Active",
}
