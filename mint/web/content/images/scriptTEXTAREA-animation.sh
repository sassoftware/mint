#/bin/sh
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
