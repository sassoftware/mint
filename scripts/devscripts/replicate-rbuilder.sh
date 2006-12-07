#!/bin/sh

# user-customizable settings
SLAVE=<HOSTNAME OF SLAVE HERE>
SSH_KEY=/root/rsync-key

# script below
MASTER_HOSTNAME=$(grep hostName /srv/rbuilder/rbuilder.conf | sed -r s/hostName\\s+//)
SLAVE_HOSTNAME=$(ssh -i /root/rsync-key dhcp241 "sh -c 'grep hostName /srv/rbuilder/rbuilder.conf'" | sed -r s/hostName\\s+//)
MAINT_CMD='echo -n 1 > /srv/rbuilder/run/maintenance.lock'

# enable maintenance mode on master and slave
sh -c "$MAINT_CMD"
ssh -i $SSH_KEY $SLAVE sh -c "$MAINT_CMD"

# wait for established connections to finish...
echo "Waiting for connections to finish..." && sleep 20 

echo "Syncing from $MASTER_HOSTNAME -> $SLAVE_HOSTNAME"
rsync --rsh "ssh -i $SSH_KEY" --delete -avx /srv/rbuilder/ $SLAVE:/srv/rbuilder/

# disable maintenance mode
rm /srv/rbuilder/run/maintenance.lock
ssh -i $SSH_KEY $SLAVE rm /srv/rbuilder/run/maintenance.lock
# fix hostnames in slave's config file:
ssh -i $SSH_KEY $SLAVE sed -i s/$MASTER_HOSTNAME/$SLAVE_HOSTNAME/g /srv/rbuilder/rbuilder.conf
# restart slave's httpd to pick up any possible config changes
ssh -i $SSH_KEY $SLAVE killall -USR1 httpd

echo "Done!"
