image_files = *.png

datadir = /usr/share/mint

dist_files = Makefile $(image_files)

all:

clean: default-clean

install: 
	mkdir -p $(DESTDIR)$(datadir)/pixmaps
	for f in $(image_files); do \
                install -m 644 $$f $(DESTDIR)$(datadir)/pixmaps/$$f; \
        done

include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
