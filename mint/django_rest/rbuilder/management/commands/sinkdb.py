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


from django.core.management.base import BaseCommand
from mint.django_rest.test_utils import TestRunner
import os

class Command(BaseCommand):
    
    help = "Replacement for syncdb. syncs db based on schema.py, not using django"
    
    def handle(self, *args, **options):
        db = TestRunner._setupDatabases()
        path_to_old_db = db[0][0][1]
        path_to_new_db = db[0][0][0].settings_dict['TEST_NAME']
        os.rename(path_to_new_db, path_to_old_db)
        print 'Setup your db'
