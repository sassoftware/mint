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
        <title>Congratulations!</title>
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

It's time to take the next step -- but what that step is depends on you:

    o You can join an existing project

    o You can create a new project

Let's go through each in more detail.

Joining a Project

If you're interested in joining a project, you probably already have a
project in mind (if not, browse through the available projects, and make
your selection).  Go to the project's homepage, and click on the "project
members" link.  Under the "project owners" heading, you'll find the
owner(s) of the project.  Click on a name, and use their contact
information to request membership in their project.

Creating a Project

To create a project, click on the "Create a new project" link under the "My
Projects" sidebar on the rBuilder Online homepage.  You'll be taken to a
form to fill out.  At a minimum you must fill in the following fields:

    o Project Name -- (alphanumeric only, 16 characters maximum)

    o Project Title -- A longer, more descriptive name for your
      project. Eg., My Custom Linux Project

Although not required, there are two other fields that you should consider filling in:

    o Project Home Page -- Entering the full URL of a page here will cause
      a link to the page to be displayed on the project's homepage.  This
      is handy for projects that have an existing homepage hosted
      elsewhere.

    o Project Description -- The text in this field is your chance to get
      the attention of prospective users and project members.  To help you
      get started, consider the writing a description that answers the
      following questions when writing a project description:

        - What is the goal of your project?
        - What technologies does your project use?
        - Why should someone join your project?
        - Why should a user download your project's software?

Finally, there are two checkboxes related to your project's mailing lists.
By default, your project will have the following two mailing lists:

    o <project-name>@lists.rpath.org -- General project-related discussion

    o <project-name>-commits@lists.rpath.org -- Messages generated when
      updates are committed into your project's Conary repository

The checkboxes allow you to add two additional mailing lists:

    o <project-name>-devel@lists.rpath.org -- Developer-centric discussion

    o <project-name>-bugs@lists.rpath.org -- Bug reports

(Once your project is created, you can add other mailing lists, if you
like.)

Once you click on "Create", your project will be created.

            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
