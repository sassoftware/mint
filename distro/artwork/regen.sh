#!/bin/sh
cd `dirname $0`

if [ ! -e /usr/bin/inkscape ] || [ ! -e /usr/bin/pngcrush ]
then
    echo Inkscape and pngcrush are required to regenerate artwork
    exit 1
fi

rm -f *.tmp

rasterfy()
{
    in="$1"
    out="$2"
    crush="$3"
    shift 3
    echo Generating "$in"
    inkscape --without-gui --file "$in" --export-png "${out}.tmp" --export-area-page "$@" || exit 1
    pngcrush -q -c "$crush" "${out}.tmp" "${out}.2.tmp" || exit 1
    mv "${out}.2.tmp" "$out"
    ls -lh "$out"
    rm -f "${out}.tmp"
}

# PNGs without transparency (strips out alpha channel)
rasterfy bootloader_splash.svg bootloader_splash.png 2 -w 640 -h 480
rasterfy bootloader_splash.svg splashy_background.png 2

# PNGs with transparency
rasterfy anaconda_splash.svg anaconda_splash.png 6
