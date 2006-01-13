#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#

stockFlavors = {
    "1#x86":    "~X,~!alternatives,!bootstrap,~builddocs,~buildtests,"
                "~desktop,~dietlibc,~emacs,~gcj,~gnome,~gtk,~ipv6,~kde,"
                "!kernel.smp,~krb,~ldap,~nptl,pam,~pcre,~perl,~!pie,"
                "~python,~qt,~readline,~!sasl,~!selinux,ssl,~tcl,"
                "tcpwrappers,~tk,~!xfce is: x86(~cmov,~i486,~i586,~i686,~mmx,~sse,~sse2)",

    "1#x86_64": "~X,~!alternatives,!bootstrap,~builddocs,"
                "~buildtests,~desktop,!dietlibc,~emacs,"
                "~gcj,~gnome,~gtk,~ipv6,~kde,~krb,~ldap,"
                "~nptl,pam,~pcre,~perl,~!pie,~python,~qt,"
                "~readline,~!sasl,~!selinux,ssl,~tcl,"
                "tcpwrappers,~tk,~!xfce is: x86_64(~3dnow,~3dnowext,~nx)",
}
