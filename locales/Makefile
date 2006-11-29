#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

TOPDIR=..

mo_files = $(wildcard */LC_MESSAGES/*.mo)

po_files = $(wildcard */LC_MESSAGES/*.po)

extra_dist = Makefile

dist_files = $(mo_files) $(po_files) $(extra_dist)

all:
	$(cd ..; tg-admin i18n collect)
	$(cd ..; tg-admin i18n compile)

install: all
	for f in $(mo_files); do \
		mkdir -p `dirname $(DESTDIR)$(localedir)/$$f`; \
		install -m755 $$f $(DESTDIR)$(localedir)/$$f; \
	done

dist: default-dist

clean: default-clean

include $(TOPDIR)/Make.rules
