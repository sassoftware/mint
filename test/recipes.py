#
# Copyright (c) 2004 Specifix, Inc.
#

testRecipe1 = """\
class TestRecipe1(PackageRecipe):
    name = 'testcase'
    version = '1.0'
    owner = 'root'
    group = 'root'
    withBinary = True
    withUse = False

    changedconfig = '%(sysconfdir)s/changedconfig'
    unchangedconfig = '%(sysconfdir)s/unchangedconfig'
    changed = '%(datadir)s/changed'
    unchanged = '%(datadir)s/unchanged'

    initialFileText = '\\n'.join([str(x) for x in range(0,10)]) + '\\n'
    fileText = initialFileText

    def modifyFiles(self):
        pass
    
    def setup(self):
        if self.withUse:
            if Use.readline:
                pass

        if self.withBinary:
            self.Run('''
cat > hello.c <<'EOF'
#include <stdio.h>

int main(void) {
    return printf("Hello, world.\\\\n");
}
EOF
	    ''')
	    self.Make('hello', preMake='LDFLAGS="-static"')
            self.Install('hello', '%(bindir)s/')
	self.Create(self.changedconfig, self.unchangedconfig,
	     self.changed, self.unchanged, contents=self.initialFileText)
	self.modifyFiles()
	self.Ownership(self.owner, self.group, '.*')

"""
        
testRecipe2="""\
class TestRecipe2(TestRecipe1):
    version = '1.1'

    fileText = TestRecipe1.fileText.replace("5", "1")

    def modifyFile(self, path):
        return 'sed -i s/^5/1/g %(destdir)s'+path

    def modifyFiles(self):
        for path in (self.changedconfig, self.changed):
            self.Run(self.modifyFile(path))

    def setup(self):
        TestRecipe1.setup(self)
"""

testRecipe3="""\
class TestRecipe3(TestRecipe1):
    version = '1.2'

    fileText = TestRecipe1.fileText.replace("6", "2")

    def modifyFile(self, path):
        return 'sed -i s/^6/2/g %(destdir)s'+path

    def modifyFiles(self):
        for path in (self.changedconfig,):
            self.Run(self.modifyFile(path))

    def setup(self):
        TestRecipe1.setup(self)
"""

testRecipe4="""\
class TestRecipe4(TestRecipe1):
    version = '1.3'

    def setup(self):
        TestRecipe1.setup(self)
	self.EtcConfig(exceptions = "/etc/.*")
"""

# like TestRecipe1, but only includes /usr/bin/hello
testRecipe5="""\
class TestRecipe5(TestRecipe1):
    version = '1.4'

    def setup(r):
        TestRecipe1.setup(r)
	r.Remove(r.changed)
	r.Remove(r.unchanged)
	r.Remove(r.changedconfig)
	r.Remove(r.unchangedconfig)
"""

testTransientRecipe1=r"""\
class TransientRecipe1(PackageRecipe):
    name = 'testcase'
    version = '1.0'
    fileText = 'bar\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""
testTransientRecipe2=r"""\
class TransientRecipe2(PackageRecipe):
    name = 'testcase'
    version = '1.1'
    fileText = 'blah\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""

libhelloRecipe="""\
class Libhello(PackageRecipe):
    name = 'libhello'
    version = '0'
    
    def setup(self):
	self.Run('''
cat > libhello.c <<'EOF'
/* libhello.c - Simple example of a shared library */

void return_one(void) {
    return 1;
}
EOF
cat > true.c <<'EOF'
int main() {
    return 0;
}
EOF
cat > user.c <<'EOF'
int main() {
    return return_one();
}
EOF
	''')
	self.Run('%(cc)s %(ldflags)s -shared -Wl,-soname,libhello.so.0 -o libhello.so.0.0 libhello.c -nostdlib')
	self.Run('%(cc)s %(ldflags)s -static -o true true.c')
	self.Run('%(cc)s %(ldflags)s -nostdlib -o user user.c libhello.so.0.0')
	self.Install('libhello.so.0.0', '%(libdir)s/libhello.so.0.0')
	self.Install('true', '%(essentialsbindir)s/ldconfig', mode=0755)
	self.Install('user', '%(essentialsbindir)s/user', mode=0755)
	self.Create('/etc/ld.so.conf', contents='/lib')
	self.Create('%(essentialbindir)s/script', 
                    contents='#!%(essentialsbindir)s/user', mode = 0755)
        self.Provides('file',  '%(essentialsbindir)s/user')
        self.ComponentSpec('runtime', '%(essentialsbindir)s/ldconfig',
                           '%(libdir)s/libhello.so.0.0')
        self.ComponentSpec('user', '%(essentialsbindir)s/user')
        self.ComponentSpec('script', '%(essentialbindir)s/script')
"""

bashRecipe="""\
class Bash(PackageRecipe):
    name = 'bash'
    version = '0'
    def setup(r):
	r.Create('%(essentialbindir)s/bash', mode=0755)
        r.Provides('file', '%(essentialbindir)s/(ba)?sh')
"""

bashMissingRecipe="""\
class Bash(PackageRecipe):
    name = 'bash'
    version = '1'
    def setup(r):
	r.Create('%(essentialbindir)s/foo', mode=0755)
"""

bashUserRecipe="""\
class BashUser(PackageRecipe):
    name = 'bashuser'
    version = '0'
    def setup(r):
	r.Create('%(essentialbindir)s/script', mode=0755,
                 contents = '#!/bin/bash')
"""

bashTroveUserRecipe="""\
class BashTroveUser(PackageRecipe):
    name = 'bashtroveuser'
    version = '0'
    def setup(r):
	r.Create('%(essentiallibdir)s/empty', mode=0644)
        r.Requires('bash:runtime', '%(essentiallibdir)s/empty')

"""

gconfRecipe="""\
class Gconf(PackageRecipe):
    name = 'gconf'
    version = '0'
    def setup(r):
	r.Create('%(sysconfdir)s/gconf/schemas/foo')
	r.Install('/bin/true', '%(bindir)s/gconftool-2', mode=0755)
"""

chkconfigRecipe="""\
class ChkconfigTest(PackageRecipe):
    name = 'testchk'
    version = '0'
    
    def setup(self):
	self.Run('''
cat > chkconfig.c <<'EOF'
int main(int argc, char ** argv) {
    int fd;
    char ** chptr;

    fd = open(\"OUT\", 0102, 0666);
    for (chptr = argv; *chptr; chptr++) {
	write(fd, *chptr, strlen(*chptr));
	if (*(chptr + 1)) write(fd, \" \", 1);
    }

    write(fd, \"\\\\n\", 1);
    close(fd);
}
EOF
''')
	self.Run('''
cat > testchk <<'EOF'
# chkconfig: 345 95 5
# description: Runs commands scheduled by the at command at the time \
#    specified when at was run, and runs batch commands when the load \
#    average is low enough.
# processname: atd
EOF
	
''')
	self.Run('%(cc)s %(ldflags)s -static -o chkconfig chkconfig.c')
	self.Install("chkconfig", "%(essentialsbindir)s/", mode = 0755)
	self.Install("testchk", "%(initdir)s/", mode = 0755)

"""

doubleRecipe1 = """
class Double(PackageRecipe):
    name = 'double'
    version = '1.0'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo1", contents = "text1")
	self.Ownership(self.owner, self.group, '.*')
"""

doubleRecipe1_1 = """
class Double(PackageRecipe):
    name = 'double'
    version = '1.1'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo1.1", contents = "text1.1")
	self.Ownership(self.owner, self.group, '.*')
"""

doubleRecipe1_2 = """
class Double(PackageRecipe):
    name = 'double'
    version = '1.2'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo1.2", contents = "text1.2")
	self.Ownership(self.owner, self.group, '.*')
"""

doubleRecipe1_3 = """
class Double(PackageRecipe):
    name = 'double'
    version = '1.3'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo1.3", contents = "text1.3")
	self.Ownership(self.owner, self.group, '.*')
"""

doubleRecipe2 = """
class Double(PackageRecipe):
    name = 'double'
    version = '2.0'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo2", contents = "text2")
	self.Ownership(self.owner, self.group, '.*')
"""

doubleRecipe2_1 = """
class Double(PackageRecipe):
    name = 'double'
    version = '2.1'
    owner = 'root'
    group = 'root'

    def setup(self):
	self.Create("/etc/foo2.1", contents = "text2.1")
	self.Ownership(self.owner, self.group, '.*')
"""

tagProviderRecipe1 = """
class TagProvider(PackageRecipe):
    name = 'tagprovider'
    version = '0'
    
    def setup(r):
	r.Run('''
cat > testtag.tagdescription <<EOF
file		/usr/libexec/conary/tags/testtag
implements      files update
implements      files remove
include		/etc/test.*
EOF
''')

	r.Run('''
cat > testtag.taghandler.c <<'EOF'
int main(int argc, char ** argv) {
    int fd;
    char ** chptr;

    fd = open(\"OUT\", 0102, 0666);
    for (chptr = argv; *chptr; chptr++) {
	write(fd, *chptr, strlen(*chptr));
	if (*(chptr + 1)) write(fd, \" \", 1);
    }

    write(fd, \"\\\\n\", 1);
    close(fd);
}
EOF
''')
	r.Run('%(cc)s %(ldflags)s -static -o testtag.taghandler testtag.taghandler.c')

	r.Install('testtag.tagdescription',
		  '%(tagdescriptiondir)s/testtag')
	r.Install('testtag.taghandler',
		  '%(taghandlerdir)s/testtag')
        # Also test tagging our own files
        r.Create('/etc/testself.1')
"""

tagProviderRecipe2 = """
class TagProvider(PackageRecipe):
    name = 'tagprovider'
    version = '1'
    
    def setup(r):
	r.Run('''
cat > testtag.tagdescription <<EOF
file		/usr/libexec/conary/tags/testtag
implements      files update
implements      files preremove
implements      files remove
implements      description update
implements      description preremove
datasource	args
include		/etc/test.*
EOF
''')

	r.Run('''
cat > testtag.taghandler.c <<'EOF'
int main(int argc, char ** argv) {
    int fd;
    char ** chptr;

    fd = open(\"OUT\", 0102, 0666);
    for (chptr = argv; *chptr; chptr++) {
	write(fd, *chptr, strlen(*chptr));
	if (*(chptr + 1)) write(fd, \" \", 1);
    }

    write(fd, \"\\\\n\", 1);
    close(fd);
}
EOF
''')
	r.Run('%(cc)s %(ldflags)s -static -o testtag.taghandler testtag.taghandler.c')

	r.Install('testtag.tagdescription',
		  '%(tagdescriptiondir)s/testtag')
	r.Install('testtag.taghandler',
		  '%(taghandlerdir)s/testtag')
        # Also test tagging our own files
        r.Create('/etc/testself.1')
"""

tagProviderRecipe3 = """
class TagProvider(PackageRecipe):
    name = 'tagprovider'
    version = '1'
    
    def setup(r):
	r.Run('''
cat > testtag.tagdescription <<EOF
file		/usr/libexec/conary/tags/testtag
implements      files update
datasource	stdin
include		/etc/test.*
EOF
''')

	r.Run('''
cat > testtag.taghandler.c <<'EOF'
int main(int argc, char ** argv) {
    int fd;
    char ** chptr;

    fd = open(\"OUT\", 0102, 0666);
    for (chptr = argv; *chptr; chptr++) {
	write(fd, *chptr, strlen(*chptr));
	if (*(chptr + 1)) write(fd, \" \", 1);
    }

    write(fd, \"\\\\n\", 1);
    close(fd);
}
EOF
''')
	r.Run('%(cc)s %(ldflags)s -static -o testtag.taghandler testtag.taghandler.c')

	r.Install('testtag.tagdescription',
		  '%(tagdescriptiondir)s/testtag')
	r.Install('testtag.taghandler',
		  '%(taghandlerdir)s/testtag')
"""

firstTagUserRecipe1 = """
class FirstTagUser(PackageRecipe):
    name = 'firsttaguser'
    version = '0'
    
    def setup(r):
	r.Run('''
cat > testfirst.1 <<EOF
first.1
EOF
''')

	r.Run('''
cat > testfirst.2 <<EOF
first.2
EOF
''')

	r.Install('testfirst.1', '/etc/testfirst.1')
	r.Install('testfirst.2', '/etc/testfirst.2')
	r.TagSpec('testtag', '/etc/test.*')
"""

secondTagUserRecipe1 = """
class SecondTagUser(PackageRecipe):
    name = 'secondtaguser'
    version = '0'
    
    def setup(r):
	r.Run('''
cat > testsecond.1 <<EOF
second.1
EOF
''')

	r.Install('testsecond.1', '/etc/testsecond.1')
	r.TagSpec('testtag', '/etc/test.*')
"""

linkRecipe1 = """\
class LinkRecipe(PackageRecipe):
    name = 'linktest'
    version = '1.0'
    hard = 1

    paths = ("/usr/share/foo", "/usr/share/bar")

    initialFileText = '\\n'.join([str(x) for x in range(0,10)]) + '\\n'
    fileText = initialFileText

    def setup(r):
        r.Create(r.paths[0], contents=r.initialFileText)
        for path in r.paths[1:]:
            if r.hard:
                r.Run("ln %%(destdir)s/%s %%(destdir)s/%s" % (r.paths[0], path))
            else:
                r.Run("ln -s %s %%(destdir)s/%s" % (r.paths[0], path))
"""

linkRecipe2 = """\
class LinkRecipe2(LinkRecipe):
    name = 'linktest'
    version = '1.1'

"""

linkRecipe3 = """\
class LinkRecipe3(LinkRecipe):
    name = 'linktest'
    version = '1.2'

    paths = ("/usr/share/foo", "/usr/share/bar", "/usr/share/foobar")
"""

# two link groups, both linkgroups have the same contents sha1
linkRecipe4 = """\
class LinkRecipe(PackageRecipe):
    name = 'linktest'
    version = '1.0'
    hard = 1

    paths = ('/usr/share/lg1-1',
             '/usr/share/lg1-2',
             '/usr/share/lg2-1',
             '/usr/share/lg2-2')

    initialFileText = '\\n'.join([str(x) for x in range(0,10)]) + '\\n'
    fileText = initialFileText

    def setup(r):
        r.Create(r.paths[0], contents=r.initialFileText)
        r.Run("ln %%(destdir)s/%s %%(destdir)s/%s" % (r.paths[0],
                                                      r.paths[1]))
        r.Create(r.paths[2], contents=r.initialFileText)
        r.Run("ln %%(destdir)s/%s %%(destdir)s/%s" % (r.paths[2],
                                                      r.paths[3]))
"""

idChange1 = """\
class IdChange1(PackageRecipe):
    name = 'idchange'
    version = '1.0'

    paths = [ "/etc/foo", "/etc/bar" ]

    fileText = '\\n'.join([str(x) for x in range(0,10)]) + '\\n'

    def setup(r):
        for path in r.paths:
            r.Create(path, contents=r.fileText)
"""

idChange2 = """\
class IdChange2(IdChange1):
    paths = [ "/etc/foo" ]
    fileText = IdChange1.fileText
    fileText.replace("5", "10")
    version = '1.1'
"""

idChange3 = """\
class IdChange3(IdChange1):
    paths = [ "/etc/foo", "/etc/bar" ]
    fileText = IdChange1.fileText
    fileText.replace("6", "11")
    version = '1.2'
"""

testUnresolved = """\
class Unresolved(PackageRecipe):
    name = 'testcase'
    version = '1.0'
    
    def setup(r):
        r.Create('/usr/bin/test', mode=0755)
        r.Requires('bar:foo', '/usr/bin/test')
"""

testTroveDepA = """\
class A(PackageRecipe):
    name = 'a'
    version = '1.0'
    
    def setup(r):
        r.Create('/usr/bin/a', mode=0755)
"""

testTroveDepB = """\
class B(PackageRecipe):
    name = 'b'
    version = '1.0'
    
    def setup(r):
        r.Create('/usr/bin/b', mode=0755)
        r.Requires('a:runtime', '/usr/bin/b')
"""


# these test updating a config file from a version which will no longer
# exist (and be cleared from the content store) to a new one
simpleConfig1 = """\
class SimpleConfig1(PackageRecipe):
    name = 'simpleconfig'
    version = '1.0'

    def setup(r):
        r.Create("/etc/foo", contents = "text 1")
"""

simpleConfig2 = """\
class SimpleConfig2(PackageRecipe):
    name = 'simpleconfig'
    version = '2.0'

    def setup(r):
        r.Create("/etc/foo", contents = "text 2")
"""

testRecipeTemplate = """\
class TestRecipe%(num)d(PackageRecipe):

    name = 'test%(num)d'
    version = '%(version)s'
    buildRequires = [ %(requires)s ]

    %(header)s

    %(flags)s

    def setup(r):

        %(flavor)s

        r.Create('/usr/bin/test%(num)s',contents='''\
#!/bin/sh
echo "This is test%(num)s"
%(fileContents)s
''', mode=0755)

        if %(binary)s:
            r.Run('''
cat > hello.c <<'EOF'
#include <stdio.h>

int main(void) {
    return printf("Hello, world.\\\\n");
}
EOF
	        ''')
	    r.Make('hello', preMake='LDFLAGS="-static"')
            r.Install('hello', '%%(bindir)s/')
        %(content)s
        %(subpkgs)s
        %(tagspec)s
        %(fail)s
"""

def createRecipe(num, requires=[], fail=False, content='', 
                 packageSpecs=[],
                 subPackages = [], version='1.0', localflags=[], flags=[],
                 header='', fileContents='', tag=None, binary=False):
    reqList = []
    for req in requires:
        reqList.append("'test%d:runtime'" % req)
    subs = {}
    subs['requires'] = ', '.join(reqList)
    subs['version'] = version
    subs['num'] = num
    subs['content'] = content
    subs['fileContents'] = fileContents
    subs['header'] = header
    subs['binary'] = binary
    subpkgStrs = []
    flagStrs = []
    flavorStrs = []
    if localflags and not isinstance(localflags, (tuple, list)):
        localflags = [localflags]

    for flag in localflags:
        flagStr = 'Flags.%s = True' % flag
        flavorStr = 'if Flags.%s: pass' % flag
        flagStrs.append(flagStr)
        flavorStrs.append(flavorStr)

    if tag:
        subs['tagspec'] = "r.TagSpec('%s', '/usr/bin/test1')" % tag
    else:
        subs['tagspec'] = ''
        

    if flags and not isinstance(flags, (tuple, list)):
        flags = [flags]
    for flag in flags:
        flavorStr = 'if %s: pass' % flag
        flavorStrs.append(flavorStr)
    subs['flags'] = '\n    '.join(flagStrs)
    subs['flavor'] = '\n        '.join(flavorStrs)

    # add indentation
    subpkgStrs.append('\n        '.join(packageSpecs))

    for subpkg in subPackages:
        subpkgStr = '''
        r.Create('%%(thisdocdir)s/README-%(subpkg)s')
        r.Create('/tmp/runtime-%(subpkg)s')
        r.PackageSpec('%(name)s-%(subpkg)s', 'README-%(subpkg)s')
        r.PackageSpec('%(name)s-%(subpkg)s', 'runtime-%(subpkg)s')
              ''' % { 'name' : ('test%d' % num), 'subpkg' : subpkg } 
        subpkgStrs.append(subpkgStr)

    subs['subpkgs'] = '\n'.join(subpkgStrs)

    if fail:
        subs['fail'] = 'r.Run("exit 1")'
    else:
        subs['fail'] = ''
    return testRecipeTemplate % subs

fileTypeChangeRecipe1="""\
class FileTypeChange(PackageRecipe):
    name = 'filetypechange'
    version = '1'
    def setup(r):
	r.Create('%(essentialbindir)s/foo', mode=0755, contents = 'some text')
"""

fileTypeChangeRecipe2="""\
class FileTypeChange(PackageRecipe):
    name = 'filetypechange'
    version = '2'
    def setup(r):
        r.Run("mkdir %(destdir)s%(essentialbindir)s")
        r.Run("ln -s foo %(destdir)s%(essentialbindir)s/foo")
"""
