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

class Command(BaseCommand):
    help = "Create the full rBuilder schema."

    def handle(self, *args, **options):
        db = dbstore.connect(settings.DATABASE_NAME, 'sqlite')
        version = schema.loadSchema(db, should_migrate=True)
        print "Migrated rBuilder schema to %s" % version
