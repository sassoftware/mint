#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

(PROJECTNAME_ASC, PROJECTNAME_DES, LASTMODIFIED_ASC, LASTMODIFIED_DES, \
 CREATED_ASC, CREATED_DES, NUMDEVELOPERS_ASC, NUMDEVELOPERS_DES, \
 ACTIVITY_ASC, ACTIVITY_DES) = range(0, 10)

descindex = 2
desctrunclength = 300

# FIXME sqlbase has been badly mangled due to sqlite3 not handling "group by" and "order by" combined with joins in any semblance of a sane fashion. the code below is a workaround. original sqlbase is included in comments. note that group by and having alteration should probably be worked into original code. it's faster.

#sqlbase = """SELECT Projects.projectId, Projects.hostname, Projects.name, Projects.description,
#    IFNULL(MAX(Commits.timestamp), Projects.timeCreated) AS timeModified
#        FROM
#    Projects
#        LEFT JOIN Commits ON
#    Projects.projectId=Commits.projectId
#        WHERE Projects.hidden=0
#        GROUP BY Projects.projectId
#        ORDER BY %s
#        LIMIT %d
#        OFFSET %d
#"""

sqlbase = """
    SELECT projectId, hostname, name, description, timeModified
        FROM (SELECT
                  Projects.projectId AS projectId,
                  Projects.hostname AS hostname,
                  Projects.name AS name,
                  LOWER(Projects.name) AS lowerName,
                  Projects.description AS description,
                  IFNULL(TM.timeModified, Projects.timeCreated)
                      AS timeModified,
                  CASE WHEN TM.timeModified IS NULL THEN 1 ELSE 0 END
                      AS fledgling,
                  (SELECT COUNT(*)
                   FROM Commits AS RC
                   WHERE RC.projectId = Projects.projectId
                   AND RC.timestamp >
                       IFNULL((SELECT MAX(C.timestamp) - 604800
                               FROM Commits AS C), 0)) AS recentCommits,
                  timeCreated,
                  (SELECT COUNT(userId) FROM ProjectUsers AS PU
                   WHERE PU.projectId = Projects.projectId) AS numDevs,
                  Projects.external AS external,
                  Projects.hidden AS hidden
              FROM Projects
              LEFT OUTER JOIN (SELECT projectId, MAX(timestamp) AS timeModified
              FROM Commits GROUP BY projectId) AS TM ON
              Projects.projectId = TM.projectId
              %s) AS P
    %s
    ORDER BY %s
    LIMIT ?
    OFFSET ?
"""

ordersql = {
    PROJECTNAME_ASC:   "lowerName ASC",
    PROJECTNAME_DES:   "lowerName DESC",
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
