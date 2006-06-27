<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
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
        <a href="${cfg.basePath}help">Help</a>
        <a href="#">Overview</a>
    </div>

    <head>
        <title>${formatTitle('Help: Overview')}</title>
    </head>

    <body>
        <div class="layout" id="help">
            <h3>An Overview of ${cfg.productName}</h3>

            <p>rPath's mission is to provide system software that is
            easily tailored to suit unique application needs.</p>

            <p>As part of that mission, we've deployed
            ${cfg.productName} for you to use.</p>

            <p>${cfg.productName} provides the infrastructure necessary
            to support the development of:</p>

            <ul>
                <li><a href="http://wiki.rpath.com/wiki/Conary">Conary</a>-based
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
                (&lt;project-name&gt;.${cfg.projectDomainName})</li>

                <li>Project-specific mailing lists</li>

                <li>(For projects developing Conary-based
                distributions) Storage space for ISO images (known as
                products) generated from the project's software</li>
            </ul>

            <p>${cfg.productName} also provides a way to browse and
            search projects and packages, making it a single source for
            all Conary-based software development.</p>

            <p>Need more details?  Pick the link that best matches your
            interest:</p>

            <ul>
                <li>I'm a <a
                href="${cfg.basePath}help?page=dev-tutorial">Developer</a></li>

                <li>I'm a <a href="${cfg.basePath}help?page=user-tutorial">User</a></li>
            </ul>
        </div>
    </body>
</html>
