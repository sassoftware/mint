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


bigdelay=100
smalldelay=15
convert -loop 0 \
    -delay $bigdelay \
    -dispose background \
    final.png \
    -dispose background \
    -delay $smalldelay \
    collapse7.png \
    -dispose background \
    collapse6.png \
    -dispose background \
    collapse5.png \
    -dispose background \
    collapse4.png \
    -dispose background \
    collapse3.png \
    -dispose background \
    collapse2.png \
    -dispose background \
    collapse1.png \
    -dispose background \
    -delay $bigdelay \
    expanded.png \
    -transparent '#FFFFFF' \
    expand.gif
convert -loop 0 \
    -delay $bigdelay \
    -dispose background \
    expanded.png \
    -dispose background \
    -delay $smalldelay \
    collapse1.png \
    -dispose background \
    collapse2.png \
    -dispose background \
    collapse3.png \
    -dispose background \
    collapse4.png \
    -dispose background \
    collapse5.png \
    -dispose background \
    collapse6.png \
    -dispose background \
    collapse7.png \
    -dispose background \
    -delay $bigdelay \
    final.png \
    -transparent '#FFFFFF' \
    collapse.gif
#convert -transparent '#FFFFFF' collapse.gif collapse-transparent.gif
