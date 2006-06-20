#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#

stockFlavors = {
    "1#x86":
        "~MySQL-python.threadsafe, ~X, ~!alternatives, ~!bootstrap,"
        "~!builddocs, ~buildtests, ~desktop, ~dietlibc, ~emacs, ~gcj,"
        "~glibc.tls, ~gnome, ~!grub.static, ~gtk, ~ipv6, ~kde,"
        "~!kernel.debug, ~!kernel.debugdata, ~!kernel.numa, ~krb, ~ldap,"
        "~nptl, ~!openssh.smartcard, ~!openssh.static_libcrypto, ~pam,"
        "~pcre, ~perl, ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline,"
        "~sasl, ~!selinux, ~sqlite.threadsafe, ~ssl, ~tcl, ~tcpwrappers,"
        "~tk, ~!xorg-x11.xprint is: x86(~cmov, ~i486, ~i586, ~i686, ~mmx,"
        "~sse2)",

    "1#x86_64":
        "~MySQL-python.threadsafe, ~X, ~!alternatives, ~!bootstrap,"
        "~!builddocs, ~buildtests,desktop, ~!dietlibc, ~emacs, ~gcj,"
        "~glibc.tls, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug,"
        "~!kernel.debugdata, ~!kernel.numa, ~krb, ~ldap, ~nptl,"
        "~!openssh.smartcard,~!openssh.static_libcrypto, ~pam, ~pcre,"
        "~perl, ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~sasl,"
        "~!selinux, ~sqlite.threadsafe, ~ssl, ~tcl, ~tcpwrappers, ~tk,"
        "~!xorg-x11.xprint is: x86(~i486,~i586,~i686,~sse2) x86_64",
}

stockFlavorPaths = {
    "1#x86":
        ["~MySQL-python.threadsafe, ~X, ~!alternatives, ~!bootstrap,"
        "~!builddocs, ~buildtests, ~desktop, ~dietlibc, ~emacs, ~gcj,"
        "~glibc.tls, ~gnome, ~!grub.static, ~gtk, ~ipv6, ~kde,"
        "~!kernel.debug, ~!kernel.debugdata, ~!kernel.numa, ~krb, ~ldap,"
        "~nptl, ~!openssh.smartcard, ~!openssh.static_libcrypto, ~pam,"
        "~pcre, ~perl, ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline,"
        "~sasl, ~!selinux, ~sqlite.threadsafe, ~ssl, ~tcl, ~tcpwrappers,"
        "~tk, ~!xorg-x11.xprint is: x86(~cmov, ~i486, ~i586, ~i686, ~mmx,"
        "~sse2)"],

    "1#x86_64":
        ["~X, ~!alternatives, !bootstrap, ~builddocs,"
         "~buildtests, ~desktop, ~!dietlibc, ~emacs, ~gcj,"
         "~gnome, ~gtk, ~ipv6, ~kde, ~krb, ~ldap, ~nptl,"
         "pam, ~pcre, ~perl, ~!pie, ~python, ~qt,"
         "~readline, ~!sasl, ~!selinux, ssl, ~tcl,"
         "tcpwrappers, ~tk, ~!xen, ~!xfce is: x86_64(~nx)",
         "~X, ~!alternatives, !bootstrap, ~builddocs,"
         "~buildtests, ~desktop, ~!dietlibc, ~emacs, ~gcj,"
         "~gnome, ~gtk, ~ipv6, ~kde, ~krb, ~ldap, ~nptl,"
         "pam, ~pcre, ~perl, ~!pie, ~python, ~qt,"
         "~readline, ~!sasl, ~!selinux, ssl, ~tcl,"
         "tcpwrappers, ~tk, ~!xen, ~!xfce is: x86(~cmov,"
         "~i486, ~i586, ~i686, ~mmx, ~nx, ~sse, ~sse2)"
         "x86_64(~nx)"],
}


