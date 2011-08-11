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