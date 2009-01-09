#!/bin/sh
cd `dirname $0`

if [ ! -e /usr/bin/inkscape ] || [ ! -e /usr/bin/pngcrush ]
then
    echo Inkscape and pngcrush are required to regenerate artwork
    exit 1
fi

rm -f *.tmp.png

# Straight PNG conversion
# NB: pngcrush is configured to strip out transparency;
# make a new section for files that need it.
for base in prodlogo
do
    echo Generating "$base"
    inkscape --without-gui --file "${base}.svg" --export-png "${base}.tmp.png" --export-area-canvas || exit 1
    pngcrush -q -c 2 "${base}.tmp.png" "${base}.png" || exit 1
    rm -f "${base}.tmp.png" "${base}.tmp2.png"
    ls -lh "${base}.png"
done
