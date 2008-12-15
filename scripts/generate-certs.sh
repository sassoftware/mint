#!/bin/sh
#
# Copyright (c) 2008 rPath, Inc.
# All rights reserved.
#
# Generate X.509 certificates. Currently, this is only for rMake's CA
# authentication, but it is run after initial install plus any updates
# so it works in either case.

if [[ -e /usr/sbin/gencert-rmake && ! -f /etc/rmake/ssl/ca.crt ]]
then
    mkdir -p /etc/rmake/ssl
    /usr/sbin/gencert-rmake -a \
        -o /etc/rmake/ssl/ca.crt -O /etc/rmake/ssl/ca.key \
        -e 3653 --O='Auto-Generated' --OU='rMake Client CA' \
        || exit 1
    chmod 0644 /etc/rmake/ssl/ca.crt || exit 1
    /usr/sbin/gencert-rmake -n \
        -c /etc/rmake/ssl/ca.crt -C /etc/rmake/ssl/ca.key \
        -o /etc/rmake/ssl/admin.pem -e 3653 -i /etc/rmake/ssl/index.txt \
        --O='Auto-Generated' --OU='rMake Admin Client' --site-user='admin' \
        || exit 1
fi


exit 0
