from django.core.management.base import BaseCommand
from mint.django_rest.test_utils import TestRunner


class Command(BaseCommand):
    def handle(self, *args, **options):
        TestRunner._setupDatabases()
        print 'Setup db'