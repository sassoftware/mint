image_files = *.gif *.jpg *.ico

dist_files = $(image_files)

all:

clean: default-clean

dist: default-dist

install: 
	mkdir -p $(DESTDIR)$(contentdir)/images
	for f in $(image_files); do \
                install -m 644 $$f $(DESTDIR)$(contentdir)/images/$$f; \
        done

include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
