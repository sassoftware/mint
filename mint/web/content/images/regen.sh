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

rm -f *.tmp.png

# PNGs without transparency (strips out alpha channel)
for base in prodlogo
do
    echo Generating "$base"
    inkscape --without-gui --file "${base}.svg" --export-png "${base}.tmp.png" --export-area-canvas || exit 1
    pngcrush -q -c 2 "${base}.tmp.png" "${base}.png" || exit 1
    rm -f "${base}.tmp.png" "${base}.tmp2.png"
    ls -lh "${base}.png"
done

# PNGs with transparency
for base in 
do
    echo Generating "$base"
    inkscape --without-gui --file "${base}.svg" --export-png "${base}.tmp.png" --export-area-canvas || exit 1
    pngcrush -q -c 6 "${base}.tmp.png" "${base}.png" || exit 1
    rm -f "${base}.tmp.png" "${base}.tmp2.png"
    ls -lh "${base}.png"
done
