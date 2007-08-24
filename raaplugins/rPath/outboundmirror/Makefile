#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

SUBDIRS = web srv

python_files = __init__.py repeatschedule.py

kid_files = index.kid

all: kid-build default-all

install: all raaplugins-install default-install

clean: kid-clean default-clean

include ../../../Make.rules
