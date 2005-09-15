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
        <title>Developers</title>
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
                <h3>rBuilder Online for Developers</h3>

                <p>If coding is your thing, you can use rBuilder Online to
                host your open source development project.</p>

                <p>What's a project?  It can be anything from packaging an
                app so it'll be available for use on Conary-based systems,
                to the creation of an operating system environment tailored
                for a specific purpose.</p>

                <p>What do you get?  Here's the list:</p>

                <ul>

                    <li>A Conary repository dedicated to your project</li>

                    <li>A project-specific hostname
                    (&lt;project-name&gt;.rpath.org)</li>

                    <li>Project-specific mailing lists:</li>

                        <ul>

                            <li>&lt;project-name&gt;@rpath.org</li>

                            <li>&lt;project-name&gt;-commits@rpath.org</li>

                            <li>&lt;project-name&gt;-devel@rpath.org (if
                            desired)</li>

                            <li>&lt;project-name&gt;-bugs@rpath.org (if
                            desired)</li>

                        </ul>

                        <li>A no-frills project-specific page
                        (http://&lt;project-name&gt.rpath.org/)</li>

                        <li>The ability to create "releases" (downloadable
                        ISO images) with a single mouse click</li>

                        <li>A project membership framework that allows you
                        to keep track of your project's members (people
                        able to commit changes to your project's
                        repository) and owners (people that can manage
                        project membership as well as having commit
                        access)</li>

                </ul>

                <p>How much does it cost?  Nothing &#8212; rBuilder
                Online's services are free for any open source project.</p>

                <p>Not the project creating type?  If you see an
                interesting project, offer your services to the project's
                owners.  If they accept, they'll make you a member of the
                project, and you'll be able to start contributing
                immediately.</p>

                <h4>HOW DO I GET STARTED?</h4>

                <p>First, you need to create your own rBuilder Online
                account.</p>

                <p>To do this, click on the [new account] (link to new
                account page) link at the top right-hand side of the
                rBuilder Online homepage.  You'll be taken to a form to
                fill out.  At a minimum you must fill in the following
                fields:</p>

                <ul>

                    <p>Username &#8212; Limit to no more than 16
                    characters</p>

                    <p>Email Address &#8212; This email address is strictly
                    for rPath to contact you regarding rBuilder Online</p>

                    <p>New Password &#8212; The password you'll use to
                    login to your account (must be at least 6
                    characters)</p>

                    <p>Confirm Password &#8212; Confirmation of the
                    password you entered above.</p>

                </ul>

                <p>Even though it is not required, you should strongly
                consider filling in the "Contact Information" field.  Why?
                Well, if you are going to create a project and you're
                looking for people to join, they'll be using the contents
                of this field to contact you.  (Note that whatever you
                enter here will be publicly accessible, so you should use
                notation such as "name at example dot com" to make life
                difficult for spammers.)</p>

                <p>Finally, you must check the two checkboxes entitled "I
                have read and accept the Terms of Service" and "I have read
                and accept the Privacy Policy".</p>

                <p>Click on "Register", and you will receive an email (sent
                to the email address you entered) with a confirmation link.
                Use your browser to follow the link, and you'll then be
                able to login.</p>

                <h5>Creating a New Project</h5>

                <p>If you'd like to create a new project, start the project
                creation process by clicking on the "Create a new project"
                link.  After that, the process is no more complex than
                filling in a few text fields and clicking on a "Create"
                button.</p>

                <h5>Joining an Existing Project</h5>

                <p>If you're interested in joining an already-existing
                project, go to the project's homepage, click on the
                "project members" link, and click on one of the project
                owners to get their contact information.  When you contact
                the project owner, ask them to make you a project member,
                and include your rBuilder Online username (they'll need it
                to make you a project member).</p>
            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
