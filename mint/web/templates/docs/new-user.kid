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
        <a href="/help">Help</a>
        <a href="#">New User</a>
    </div>

    <head>
        <title>${formatTitle('Help: New User Introduction')}</title>
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

                <h3>Your new rBuilder Online account is active!</h3>

                <p>It's time to take the next step &#8212; but what that
                step is depends on you:</p>

                <ul>

                    <li>You can join an existing project</li>

                    <li>You can create a new project</li>

                </ul>

                <p>Let's go through each in more detail.</p>

                <h4>Joining a Project</h4>

                <p>If you're interested in joining a project, you probably
                already have a project in mind (if not, browse through the
                available projects, and make your selection).  Go to the
                project's homepage, and click on the <tt>project
                members</tt> link.  Under the <tt>project owners</tt>
                heading, you'll find the owner(s) of the project.  Click on
                a name, and use their contact information to request
                membership in their project.</p>

                <h4>Creating a Project</h4>

                <p>To create a project, click on the <tt>Create a new
                project</tt> link under the <tt>My Projects</tt> sidebar on
                the rBuilder Online homepage.  You'll be taken to a form to
                fill out.  At a minimum you must fill in the following
                fields:</p>

                <ul>

                <li><tt>Project Name</tt> &#8212; (alphanumeric only, 16
                characters maximum)</li>

                <li><tt>Project Title</tt> &#8212; A longer, more
                descriptive name for your project. For example, "My Custom
                Linux Project"</li>

                </ul>

                <p>Although not required, there are two other fields that
                you should consider filling in:</p>

                <ul>

                <li><tt>Project Home Page</tt> &#8212; Entering the full
                URL of a page here will cause a link to the page to be
                displayed on the project's homepage.  This is handy for
                projects that have an existing homepage hosted
                elsewhere.</li>

                <li><tt>Project Description</tt> &#8212; The text in this
                field is your chance to get the attention of prospective
                users and project members.  To help you get started,
                consider the writing a description that answers the
                following questions when writing a project description:

                    <li>What is the goal of your project?</li>

                    <li>What technologies does your project use?</li>

                    <li>Why should someone join your project?</li>

                    <li>Why should a user download your project's
                    software?</li>

                </li>

                </ul>

                <p>Finally, there are two checkboxes related to your
                project's mailing lists.  By default, your project will
                have the following two mailing lists:</p>

                <ul>

                <li>&lt;project-name&gt;@lists.rpath.org &#8212; General
                project-related discussion</li>

                <li>&lt;project-name&gt;-commits@lists.rpath.org &#8212;
                Messages generated when updates are committed into your
                project's Conary repository</li>

                </ul>

                <p>The checkboxes allow you to add two additional mailing
                lists:</p>

                <ul>

                <li>&lt;project-name&gt;-devel@lists.rpath.org &#8212;
                Developer-centric discussion</li>

                <li>&lt;project-name&gt;-bugs@lists.rpath.org &#8212; Bug
                reports</li>

                </ul>

                <p>(Once your project is created, you can add other mailing
                lists, if you like.)</p>

                <p>Once you click on <tt>Create</tt>, your project will be
                created.</p>

                <h4>What Next?</h4>

                <p>If you're interested in creating a customized
                distribution, the tutorial on <a
                href="http://wiki.conary.com/DerivativeDistroTutorial">this
                page</a> is a good place to start.</p>

            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
