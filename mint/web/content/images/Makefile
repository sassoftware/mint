image_files = *.gif *.jpg

favicon = favicon/rpath-16x16-favicon.ico

dist_files = Makefile $(image_files) $(favicon)

all:

clean: default-clean

dist: default-dist

install: 
	mkdir -p $(DESTDIR)$(contentdir)/images
	for f in $(image_files); do \
                install -m 644 $$f $(DESTDIR)$(contentdir)/images/$$f; \
        done
	install -m 644 favicon/rpath-16x16-favicon.ico $(DESTDIR)$(contentdir)/images/rpath-16x16-favicon.ico

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
