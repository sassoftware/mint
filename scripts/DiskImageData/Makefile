bin_files = init.sh
data_files = fstab \
	     ifcfg-eth0 \
	     post-kernel-tag-scripts \
	     pre-tag-scripts \
	     hosts \
	     network \
	     post-tag-scripts \
             vmdisk.vmdk \
             vmwareesx.vmx \
	     vmwareplayer.vmx \
	     mouse \
	     xorg.conf \
	     keyboard \
	     vpc.vmc \
	     i18n	\
	     clock	\
	     ova.xml.in

datadir = /usr/share/rbuilder

dist_files = Makefile $(data_files) $(bin_files)

all:

clean: default-clean

dist: default-dist

install: 
	mkdir -p $(DESTDIR)$(datadir)/DiskImageData
	for f in $(data_files); do \
                install -m 644 $$f $(DESTDIR)$(datadir)/DiskImageData/$$f; \
        done
	for f in $(bin_files); do \
		 install -m 755 $$f $(DESTDIR)$(datadir)/DiskImageData/$$f; \
        done

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
