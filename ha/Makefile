#
# Copyright (c) SAS Institute Inc.
#

generated_files = rpath_ha/manifests/managed_services.pp

managed_services = \
	postgresql-rbuilder \
	pgbouncer \
	gunicorn \
	nginx \
	rmake-messagebus \
	jabberd \
	mcp-dispatcher \
	jobmaster \
	rmake \
	rmake-node \
	rmake3 \
	rmake3-node \
	rbuilder-credstore \
	rbuilder-ha-cron \


prim_pat = '%',
prim_list = $(patsubst %,$(prim_pat),$(managed_services))


all: default-all $(generated_files)

install: default-install $(generated_files)
	mkdir -p $(DESTDIR)/usr/share/puppet/modules
	cp -r rpath_ha $(DESTDIR)/usr/share/puppet/modules/
	install -D -m0644 rbuilder.pp $(DESTDIR)/usr/share/rbuilder/ha/rbuilder.pp.example
	install -D -m0755 pri-lost-after-sb.sh $(DESTDIR)/usr/share/rbuilder/ha/pri-lost-after-sb.sh
	install -D -m0755 rbuilder-ha-cron $(DESTDIR)/usr/share/rbuilder/ha/rbuilder-ha-cron

clean: default-clean


rpath_ha/manifests/managed_services.pp: service_template.pp group_template.pp Makefile
	echo "class rpath_ha::managed_services {" > "$@.tmp"
	for service in ${managed_services}; do \
		echo "rpath_ha::managed_service { '$$service': }" >> "$@.tmp"; \
	done
	echo "\$$services = [${prim_list}]" >> "$@.tmp"
	echo "}" >> "$@.tmp"
	mv "$@.tmp" "$@"


include ../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
