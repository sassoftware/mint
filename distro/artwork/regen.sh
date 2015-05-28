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
for x in anaconda_first anaconda_splash
do
    rasterfy $x.svg $x.png 6
done
