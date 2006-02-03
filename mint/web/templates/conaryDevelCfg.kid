<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        releases = project.getReleases(showUnpublished = False)
        commits = project.getCommits()
        protocol = 'http'
        if cfg.SSL:
            protocol = 'https'
    ?>
    <head>
        <title>${formatTitle('Conary Development Environment: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div class="layout" class="helpPage">
            <h2>${project.getNameForDisplay(maxWordLen = 50)}</h2>
            <h3>Setting up Your Conary Development Environment</h3>

                <p>NOTE: You will need the following pieces of
                information in order to start building packages for
                this project:</p>

                <ul>
                    <li>Build Label: <strong><tt>${project.getLabel()}</tt></strong></li>
                    <li>Your ${cfg.productName} username and password</li>
                </ul>

                <h3>Getting Started</h3>

                    <p>If you're new to packaging with Conary, you need
                    to create some directories and Conary configuration
                    files; there are many different ways to do this,
                    but the following approach works equally well when
                    packaging for single or multiple projects.</p>

                    <h4>Creating Directories</h4>

                        <p>In order to keep all your Conary-related
                        packaging in one place, start by creating a
                        top-level directory &#8212; in this example,
                        we'll call it <tt>conary</tt>, and put it in
                        our login directory.  All your Conary packaging
                        &#8212; no matter what the project &#8212; will
                        be done under this directory.</p>

                        <p>Next, you must create a directory tree
                        (under <tt>~/conary</tt>) that will contain all
                        the files related to this project.  The name of
                        the root directory for this tree should clearly
                        identify the project; some people use the
                        hostname of the project's repository, while
                        others use just the project's name &#8212; the
                        choice is yours.  In this example, we'll use
                        <tt>${project.getFQDN()}</tt>.</p>

                        <p>Once you've decided on a name for this
                        project's directory, create it and populate it
                        with subdirectories named <tt>src</tt>,
                        <tt>builds</tt>, and <tt>cache</tt>.  Our
                        example directory tree looks like this:</p>

                        <ul>
                            <li><strong><tt>~/conary/${project.getFQDN()}/src</tt></strong></li>
                            <li><strong><tt>~/conary/${project.getFQDN()}/builds</tt></strong></li>
                            <li><strong><tt>~/conary/${project.getFQDN()}/cache</tt></strong></li>
                        </ul>

                        <p>The <tt>src</tt> directory will have
                        subdirectories (one for each package), each
                        containing a <tt>CONARY</tt> file created by
                        Conary, and a recipe file (along with any other
                        files that might be necessary to properly
                        package the software).</p>

                        <p>The <tt>builds</tt> directory is where
                        packages will actually be built.</p>

                        <p>The <tt>cache</tt> directory is used to
                        store the source archives downloaded during the
                        build process, avoiding the necessity of
                        repetitively downloading the same source
                        archive each time a build is attempted.</p>

                    <h4>Setting Up Conary's Configuration Files</h4>

                        <p>Next, it's time to set up Conary's
                        configuration files.  The first file to
                        consider is <tt>/etc/conaryrc</tt> &#8212; this
                        file should contain only system-wide settings;
                        no settings related to packaging should be
                        present in this file.</p>

                        <p>Create a file called <tt>.conaryrc</tt> in
                        your home directory.  This file should contain
                        Conary settings that are specific to you, such
                        as:</p>

                        <ul>
                            <li><strong><tt>name &lt;your-name&gt;</tt></strong></li>
                            <li><strong><tt>contact &lt;your-contact-info&gt;</tt></strong></li>
                        </ul>

                        <p>Finally, create a file called
                        <tt>conaryrc</tt> (<em>note the absence of a
                        dot</em>) in the
                        <tt>~/conary/${project.getFQDN()}/</tt>
                        directory.  This file should contain Conary
                        settings that are exclusively related to this
                        project, such as:</p>

                        <ul>
                            <li><strong><tt>buildLabel ${project.getLabel()}</tt></strong></li>
                            <li><strong><tt>buildPath (full path to the builds subdirectory)</tt></strong></li>
                            <li><strong><tt>lookaside (full path to the cache subdirectory)</tt></strong></li>
                            <li><strong><tt>user *.rpath.org username password</tt></strong></li>
                        </ul>

                        <p>Because Conary only reads the
                        <tt>conaryrc</tt> file when it is in the
                        current directory, you must create a symlink
                        for it in the <tt>src</tt> subdirectory.  This
                        way, when you issue a <tt>cvc newpkg</tt> or
                        <tt>cvc checkout</tt> command in the
                        <tt>src</tt> subdirectory, Conary will be
                        configured to respond properly.</p>

                        <p>Note also that, whenever you issue a <tt>cvc
                        newpkg</tt> or <tt>cvc checkout</tt> command,
                        you should then create a symlink to
                        <tt>../../conaryrc</tt> in the newly-created
                        directory.  By doing this, Conary commands will
                        work as expected while in that directory as
                        well.</p>


                        <p>Now you're ready to start packaging!  If
                        you're new to packaging with Conary, you can
                        find information on the <a
                        href="http://wiki.conary.com/">Conary
                        Wiki</a>.</p>

            <h3>Signing Packages With OpenPGP Keys</h3>

                <p>Conary includes support for signed packages using
                OpenPGP keys.  Projects have the option of using this
                feature or not; ask this project's owners if you should
                be signing packages or not.  They will also help you
                get a OpenPGP key pair if you do not already have one
                (or the project requires the creation a special key
                pair).</p>

                <p>If this project's owners require you to sign
                packages, you must first upload your public key to this
                project's repository.  This can be done by logging in
                to ${cfg.productName} and clicking on the <tt>upload a
                package signing key</tt> link present below your
                username in the upper right-hand corner of the page.
                You'll be taken to a page where your public key can be
                uploaded.</p>

                <p>Next, you must configure Conary to use your key.</p>

                <p>To do this, you will be using two Conary
                configuration options:</p>

                <ul>
                    <li><tt><strong>signatureKey</strong></tt></li>
                    <li><tt><strong>signatureKeyMap</strong></tt></li>
                </ul>

                <p>These two options interact in a specific way.  It is
                possible to build up a list of keys (along with the
                circumstances in which they should be used) by
                repetitively including <tt>signatureKeyMap</tt> lines
                in one or more Conary configuration files.  The first
                <tt>signatureKeyMap</tt> line that matches will be
                used.</p>

                <p>However, as soon as Conary encounters a
                <tt>signatureKey</tt> line, all previous
                <tt>signatureKeyMap</tt> <em>and</em>
                <tt>signatureKey</tt> settings are ignored, and the
                setting of the current <tt>signatureKey</tt> is used
                instead.</p>

                <p>As with configuring your Conary development
                environment, there are many different ways of
                configuring Conary to use OpenPGP keys.  However, the
                following approach works well whether you'll be signing
                packages for one or many projects.</p>

                <p>First, edit <tt>.conaryrc</tt>, and include the
                following line <em>at the top</em>:</p>

                <p><tt><strong>signatureKey    None</strong></tt></p>

                <p>This line ensures that, if any system-wide
                signature-related settings were made in
                <tt>/etc/conaryrc</tt>, they will be ignored.  Note
                that, if you also do not include any other key-related
                settings in this (or any project-specific
                <tt>conaryrc</tt> file), Conary will never attempt to
                use a key to sign any packages.</p>

                <p>Next, add a <tt>signatureKeyMap</tt> entry for this
                project <em>after</em> the <tt>signatureKey</tt> entry
                at the top.  The <tt>signatureKeyMap</tt> uses the
                following format:</p>

                <p><tt><strong>signatureKeyMap  &lt;regular-expression&gt; &lt;key-fingerprint&gt;</strong></tt></p>

                <p>(Where
                <tt><strong>&lt;regular-expression&gt;</strong></tt>
                represents a regular expression matching this project's
                label, and
                <tt><strong>&lt;key-fingerprint&gt;</strong></tt>
                represents the fingerprint of the desired key.)</p>

                <p>Here is an example <tt>signatureKeyMap</tt> line
                (using a invalid fingerprint; use <tt>gpg --list-keys
                --fingerprint</tt> to obtain the fingerprint for your
                key):</p>

                <p><tt><strong>signatureKeyMap ${project.getLabel()} B1EE 5468 2429 249E 3C24  FD50 E55A 1E3D 2417 65F8</strong></tt></p>

                <p>Note that, if you wanted to ensure that this key
                would be used on all this project's branches, you could
                replace everything after the <tt>@</tt> with
                <tt>.*</tt>.  Also note that, strictly speaking, the
                dots in this project's label should be replaced with
                <tt>\.</tt> (remember, this is a regular expression).
                However, leaving them as-is will still work (though
                doing so does leave open the possibility of inadvertent
                matches).</p>

                <p>The following formats are acceptable for expressing
                your key's fingerprint &#8212; all would reference the
                same key:</p>

                <ul>
                    <li><strong><tt>B1EE 5468 2429 249E 3C24  FD50 E55A 1E3D 2417 65F8</tt></strong></li>
                    <li><strong><tt>B1EE54682429249E3C24FD50E55A1E3D241765F8</tt></strong></li>
                    <li><strong><tt>E55A1E3D241765F8</tt></strong></li>
                </ul>

                <p>If you need additional keys for additional projects
                (or even for specific branches in a single project),
                add the appropriate <tt>signatureKeyMap</tt> line(s),
                one after the other, in your <tt>.conaryrc</tt> file
                (after the <tt>signatureKey</tt> line at the top of the
                file, of course).  In this way, the settings for all
                the keys Conary is configured to use are in one
                place.</p>
        </div>
    </body>
</html>
