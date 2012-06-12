#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django.conf import settings
from django.core.management.base import BaseCommand

from conary import dbstore
from mint.db import schema
from mint.django_rest.rbuilder import models

class Command(BaseCommand):
    help = "Create the full rBuilder schema."

    def handle(self, *args, **options):
        dbVersion = models.DatabaseVersion(
            version=schema.RBUILDER_DB_VERSION.major,
            minor=schema.RBUILDER_DB_VERSION.minor)
        dbVersion.save()
        db = dbstore.connect(settings.DATABASES['default']['NAME'], 'sqlite')
        version = schema.loadSchema(db, should_migrate=True)
        print "Migrated rBuilder schema to %s" % version
