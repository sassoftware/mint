image_files = *.gif *.jpg

favicon = favicon/rpath-16x16-favicon.ico

dist_files = Makefile $(image_files)

all:

clean: default-clean

dist: default-dist
	cp -a $(favicon) $(DISTDIR)/$(DIR)/favicon.ico

install: 
	mkdir -p $(DESTDIR)$(contentdir)/images
	for f in $(image_files) favicon.ico; do \
                install -m 644 $$f $(DESTDIR)$(contentdir)/images/$$f; \
        done

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
