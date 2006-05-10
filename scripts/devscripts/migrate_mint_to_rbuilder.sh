#!/bin/sh
# migrate mint -> rbuilder

CONFIGFILES="/srv/rbuilder/rbuilder.conf /srv/rbuilder/iso_gen.conf /srv/rbuilder/installable_iso.conf /etc/httpd/conf.d/00mint.conf /etc/httpd/conf.d/mint.include /etc/fstab"

if [ `whoami` != 'root' ]; then
    echo "Migration script must be run as root."
    exit 1
fi

if [ ! -d /srv/rbuilder -a ! -d /srv/mint ]; then
    echo "rBuilder is not installed; nothing to migrate."
    exit 1
fi

if [ ! -d /srv/mint -a -d /srv/rbuilder ]; then
    echo "Migration has already occurred."
    exit 1
fi

# start the migration here
mv /srv/mint/mint.conf /srv/mint/rbuilder.conf
mv /srv/mint /srv/rbuilder
[ -d /export/mint ] && mv /export/mint /export/rbuilder

for f in $CONFIGFILES; do
    sed -i".bak" -e '
        s|/srv/mint/|/srv/rbuilder/|g
        s|/srv/rbuilder/mint.conf|/srv/rbuilder/rbuilder.conf|g
    ' $f
    if [ $? -ne 0 ]; then
        echo "warning: failed to update file $f (may not exist)"
    fi
done

# restart the webserver
killall -USR1 httpd > /dev/null 2>&1

echo "Migration complete; you may need to restart any running job servers."
exit 0
