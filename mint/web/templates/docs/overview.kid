<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels ?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../library.kid', '../layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <?python
        ownsProjects = False
        if projectList:
            for project, level in projectList:
                if level == userlevels.OWNER:
                    ownsProjects = True
                    break
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="/help">Help and Feedback</a>
    </div>

    <head>
        <title>Overview ${cfg.productName}</title>
    </head>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>

        <td id="main">
            <div class="pad">
                <h3>An Overview of rBuilder Online</h3>

                <p>rPath's mission is to provide system software that is
                easily tailored to suit unique application needs.</p>

                <p>As part of that mission, we've deployed rBuilder Online
                for you to use.</p>

                <p>rBuilder Online provides the infrastructure necessary to
                support the development of:</p>

                <ul>
                    <li><a href="http://wiki.conary.com/">Conary</a>-based
                    Linux distributions</li>

                    <li>Open source software packaged with Conary</li>
                </ul>

                <p>Development is done in projects, which consist of:</p>

                <ul>
                    <li>Project owners, who create and manage the project
                    on a day-to-day basis</li>

                    <li>Project members, who join the project to support
                    the project's development effort</li>

                    <li>A Conary repository to hold all the packaged
                    software specific to the project</li>

                    <li>A project-specific hostname
                    (&lt;project-name&gt;.rpath.org)</li>

                    <li>Project-specific mailing lists</li>

                    <li>(For projects developing Conary-based
                    distributions) Storage space for ISO images (known as
                    releases) generated from the project's software</li>
                </ul>

                <p>rBuilder Online also provides a way to browse and search
                projects and packages, making it a single source for all
                Conary-based software development.</p>

                <p>Need more details?  Pick the link that best matches your
                interest:</p>

                <ul>
                    <li>I'm a <a
                    href="/help?page=dev-help">Developer</a></li>

                    <li>I'm a <a href="/help?page=user-help">User</a></li>
                </ul>
            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
