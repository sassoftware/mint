#!/bin/sh
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Generate X.509 certificates. This script is run on first boot after an
# install, plus after any subsequent updates.

if [ -x /usr/sbin/gencert-rmake ]
then
    # rMake cert authority + admin client cert
    if [ ! -f /etc/rmake/ssl/ca.crt ]
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

    # Generate the plethora of managed certificates, including ones for httpd
    # and jabberd.
    /usr/share/rbuilder/scripts/pki-tool --initialize -q 2>&1 >>/var/log/rbuilder/scripts.log
fi

# Create the combined key/cert file for rPA if it doesn't already have one.
if [[ -f /etc/ssl/private/localhost.key &&  ! -f /etc/ssl/pem/raa.pem ]]
then
    mkdir -p /etc/ssl/pem
    touch /etc/ssl/pem/raa.pem
    chmod 0600 /etc/ssl/pem/raa.pem

    cat /etc/ssl/certs/localhost.crt /etc/ssl/private/localhost.key \
        >/etc/ssl/pem/raa.pem
fi


exit 0
