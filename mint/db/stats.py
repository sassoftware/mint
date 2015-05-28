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


from mint.lib import database


class CommitsTable(database.DatabaseTable):
    name = "Commits"
    fields = ['projectId', 'timestamp', 'troveName', 'version', 'userId']

    def new(self, projectId, timestamp, troveName, troveVersion, userId):
        cu = self.db.cursor()
        cu.execute("INSERT INTO Commits VALUES (?, ?, ?, ?, ?)",
            projectId, timestamp, troveName, troveVersion, userId)
        self.db.commit()
