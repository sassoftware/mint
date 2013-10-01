#!/bin/bash
/usr/lib/drbd/crm-unfence-peer.sh
/usr/lib/drbd/notify-pri-lost-after-sb.sh "$@"
