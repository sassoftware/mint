javascript_files = *.js

dist_files = $(javascript_files) Makefile

all:

install:
	mkdir -p $(DESTDIR)$(contentdir)/javascript
	for f in $(javascript_files); do \
		install -m 644 $$f $(DESTDIR)$(contentdir)/javascript/$$f; \
	done

dist: default-dist

clean: default-clean

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
