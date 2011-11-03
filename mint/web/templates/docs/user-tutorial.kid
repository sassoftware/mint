<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels, constants ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <?python
        from mint.web.templatesupport import projectText
        ownsProjects = False
        if projectList:
            for project, level in projectList:
                if level == userlevels.OWNER:
                    ownsProjects = True
                    break
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="${cfg.basePath}help">Help</a>
        <a href="#">Users</a>
    </div>

    <head>
        <title>${formatTitle('Help: Users')}</title>
    </head>

    <body>
        <div class="layout">
            <h1>rBuilder for Users</h1>

            <h2>Download and Install Complete Distributions</h2>
            <p>
                You can download and install a complete Conary-based system from
                the published releases of an rBuilder ${projectText().lower()}.  These releases may be referred
                to as <i>distributions</i> or <i>software appliances</i> depending on the
                nature of the ${projectText().lower()}.  Conary-based Linux distributions, such as <a
                href="http://www.rpath.com/rbuilder/project/rpath/">rPath
                Linux</a>, are available for free from rBuilder Online.
            </p>

            <p>
                Use the Search text box at the top of the rBuilder web interface to find a
                ${projectText().lower()} that has the release you want.  Click the <b>View Releases</b> link in
                the <i>${projectText().title()} Resources</i> menu to see a list of the ${projectText().lower()}'s published
                releases, which are each fully installable Conary-based systems representing
                distributions or software appliances.
            </p>

            <p>
                The release information displays the type of downloads
                available, such as raw hard disk images or installable CD/DVDs.  Click the
                linked name of the release, and click <b>Download</b> to download for the
                image.  For installable CD/DVD images, copy the images onto the appropriate
                media and use it to install your system.
            </p>

            <h3>Download and Install Individual Packages</h3>
            <p>
                If you are currently using a Conary-based system, and you are looking for
                software already packaged for Conary, find available packages in rBuilder and
                install them from their original ${projectText().lower()} repositories.
            </p>

            <p>
                Use the Search text box at the top of the rBuilder web interface to find a
                package that has the software you want.  Click <b>Browse Repository</b> to
                navigate the list of individual packages in the ${projectText().lower()}, each of which can be
                installed on an existing Conary-based system.
            </p>

            <p>
                Click the linked package name in the <i>Repository Browser</i> to view
                package information, and locate the ${projectText().lower()} <a
                href="http://wiki.rpath.com/wiki/Glossary?version=${constants.mintVersion}#label">label</a> as
                part of the <i>Version</i> string listed in this information.  The ${projectText().lower()}
                label for a package with a version of
                <i>/${projectText().lower()}name.rpath.org@rpl:devel/1.1-1-1</i> is
                <b>${projectText().lower()}name.rpath.org@rpl:devel</b>.  As the root user of your Conary-based
                system, use the following command to install the package from rBuilder,
                replacing &lt;package&gt; with the package name and &lt;${projectText().lower()}_label&gt; with
                the ${projectText().lower()} label:
            </p>

            <pre class="cmd">[user@host ~]# conary update &lt;package&gt;=&lt;${projectText().lower()}_label&gt;</pre>

            <h3>Keep Software Updated</h3>

            <p>Keep your distributions and installed software packages updated using
            <b>conary update</b>.  This command used with an installed package name will
            tell Conary to update the system to the latest version of that package in the
            rBuilder ${projectText().lower()}'s repository.  As the root user on the Conary-based system,
            run the following command to update a package by name: </p>

            <pre class="cmd">[user@host ~]# conary update &lt;package_name&gt;</pre>

            <p>Use this command to update your entire system at one time:</p>
            <pre class="cmd">[user@host ~]# conary updateall</pre>
            <p>Use the <a href="http://wiki.rpath.com/wiki/Conary:QuickReference?version=${constants.mintVersion}">Conary
            QuickReference</a> to reference this and other tasks used to maintain your
            Conary-based system.  </p>

            <h3>Follow or Join a ${projectText().title()}</h3>
            <p>While a Conary update for installed packages is automated, eliminating the
            need to visit a ${projectText().lower()} in rBuilder, you may choose to watch the ${projectText().lower()} in
            rBuilder.  rBuilder users
            can create a watch list available on the right side of each rBuilder page, and
            registered and unregistered users alike can subscribe to RSS
            feeds for the ${projectText().lower()}.  </p>

            <ul>
                <li> Subscribe to an RSS feed for ${projectText().lower()} release news using the RSS link on a ${projectText().lower()}'s main page</li>
                <li> <a href="http://wiki.rpath.com/wiki/rBuilder:Watch_a_Project?version=${constants.mintVersion}">Watch a ${projectText().lower()}</a> to bookmark it in your rBuilder watch list</li>
            </ul>

            <p>As an rBuilder user, you may also wish to <a
            href="http://wiki.rpath.com/wiki/rBuilder:Join_a_Project?version=${constants.mintVersion}">join
            a ${projectText().lower()}</a> to help out with testing, documentation, design, or to
            participate as a developer.</p>

            <h3>Create Your Own ${projectText().title()}</h3>
            <p>rBuilder gives you the opportunity to create a new rBuilder ${projectText().lower()}.  Use
            your ${projectText().lower()} to develop your own distributions using existing rBuilder packages
            or for incorporating new packaged software.  Instructions for joining,
            participating in, and creating an rBuilder ${projectText().lower()} is available in <a
            href="http://wiki.rpath.com/wiki/rBuilder?version=${constants.mintVersion}">rBuilder's online documentation</a>,
            and an introduction to packaging your own software for a ${projectText().lower()} is available
            in the <a href="http://wiki.rpath.com/wiki/Conary:New_Package_Tutorial?version=${constants.mintVersion}">New
            Package Tutorial</a>.</p>

            <p>For detailed instructions on these rBuilder operations and more, see the <a
            href="http://wiki.rpath.com/wiki/rBuilder?version=${constants.mintVersion}">rBuilder documentation at
            wiki.rpath.com</a>.</p>

        </div>
    </body>
</html>
