#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

(
    USERNAME_ASC,
    USERNAME_DES,
    FULLNAME_ASC,
    FULLNAME_DES,
    CREATED_ASC,
    CREATED_DES,
    ACCESSED_ASC,
    ACCESSED_DES
) = range(0, 8)

blurbindex = 5
blurbtrunclength = 300
sqlbase = """SELECT userid, username, fullname, timeCreated, timeAccessed,
blurb FROM users WHERE active=1
    ORDER BY %s
    LIMIT %d
    OFFSET %d"""

ordersql = {
    USERNAME_ASC: "LOWER(username) ASC",
    USERNAME_DES: "LOWER(username) DESC",
    FULLNAME_ASC: "LOWER(fullname) ASC",
    FULLNAME_DES: "LOWER(fullname) DESC",
    CREATED_ASC:  "timeCreated ASC",
    CREATED_DES:  "timeCreated DESC",
    ACCESSED_ASC: "timeAccessed ASC",
    ACCESSED_DES: "timeAccessed DESC"
}

orderhtml = {
    USERNAME_ASC: "Username in ascending order",
    USERNAME_DES: "Username in descending order",
    FULLNAME_ASC: "Full name in ascending order",
    FULLNAME_DES: "Full name in descending order",
    CREATED_ASC:  "Oldest users",
    CREATED_DES:  "Newest users",
    ACCESSED_ASC: "Least recently accessed",
    ACCESSED_DES: "Most recently accessed"
}
