<?xml version='1.0' encoding='UTF-8'?>
<?python from mint import userlevels ?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
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
        <a href="${cfg.basePath}help">Help</a>
        <a href="#">Users</a>
    </div>

    <head>
        <title>${formatTitle('Help: Users')}</title>
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
                <h2>${cfg.productName} for Users</h2>

                <p>Even if you're not the coding type, ${cfg.productName}
                still has a lot to offer.</p>

                <p>Already using a Conary-based system?  You came to the
                right place to look for software &#8212; browse and search
                your way to the right package, and then use Conary to
                install it right off the project's repository.</p>

                <p>Looking for a Conary-based system?  Search and/or browse
                the projects on ${cfg.productName}, and pick the one that best
                meets your needs.  Download the release ISO image(s), and
                you're off and running.</p>

                <p>Interested in a particular project?  You can keep track
                of what's going on by subscribing to the project's mailing
                list(s), or just use the project's <tt>recent releases</tt>
                RSS feed to find out when there's a new release
                available.</p>

                <p>Of course, all projects need people to help out with
                testing, documentation, and the like, so if there's an
                interesting project, feel free to <a
                href="${cfg.basePath}register">create</a> an ${cfg.productName} account,
                and offer your services to the project owners.</p>

                <h2>HOW DO I GET STARTED?</h2>

                <p>Use ${cfg.productName}'s browse and search functions to
                learn more about the projects and software available.</p>

                <p>Found an interesting project?  Here are some helpful
                hints:</p>

                <ul>

                    <li>The project's home page contains the necessary
                    Conary configuration information to install the
                    project's software on your Conary-based system.</li>

                    <li>You can keep in touch with the project by following
                    developer discussion and code commits using the
                    project's mailing lists.</li>

                    <li>The project's release page lists all available
                    releases (which are installable ISO images).</li>

                </ul>

            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
