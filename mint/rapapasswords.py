#
# Copyright (c) 2007 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

class rAPAPasswords(database.DatabaseTable):

    name = "rAPAPasswords"

    createSQL = """
                CREATE TABLE rAPAPasswords (
                    host                VARCHAR(255),
                    user                VARCHAR(255),
                    password            VARCHAR(255),
                    role                VARCHAR(255)
                )"""

    fields = [ 'host', 'user', 'password', 'role']


    def setrAPAPassword(self, host, user, password, role):
        cu = self.db.cursor()
        cu.execute("""SELECT * FROM rAPAPasswords WHERE
                      host=? AND role=?""", host, role)
        if cu.fetchone():
            try:
                cu.execute("""UPDATE rAPAPasswords SET user=?, 
                              password=? WHERE host=? AND role=?""",
                              user, password, host, role)
                self.db.commit()
            except:
                self.db.rollback()
                raise
        else:
            try:
                cu.execute("INSERT INTO rAPAPasswords VALUES (?, ?, ?, ?)",
                           host, user, password, role)
                self.db.commit()
            except:
                self.db.rollback()
                raise
        return True

    def getrAPAPassword(self, host, role):
        cu = self.db.cursor()
        cu.execute("""SELECT user, password FROM rAPAPasswords WHERE
                      host=? AND role=?""", host, role)
        id = cu.fetchone()
        if id:
            return list(id)
        else:
            return False
