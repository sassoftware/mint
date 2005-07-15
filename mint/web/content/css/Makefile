css_files = *.css

dist_files = $(css_files) Makefile

all:

install:
	mkdir -p $(DESTDIR)$(contentdir)/css
	for f in $(css_files); do \
		install -m 644 $$f $(DESTDIR)$(contentdir)/css/$$f; \
	done

dist: default-dist

clean: default-clean 

include ../../../../Make.rules
