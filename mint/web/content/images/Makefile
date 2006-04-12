image_files = *.gif *.jpg *.png favicon.ico

favicon = favicon/rpath-16x16-favicon.ico

dist_files = Makefile $(image_files)

all:
	cp -a $(favicon) favicon.ico

clean: default-clean

dist: default-dist

install: 
	mkdir -p $(DESTDIR)$(contentdir)/images
	for f in $(image_files); do \
                install -m 644 $$f $(DESTDIR)$(contentdir)/images/$$f; \
        done

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
