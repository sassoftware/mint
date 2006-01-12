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
        <a href="#">Developers</a>
    </div>

    <head>
        <title>${formatTitle('Help: Developers')}</title>
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
                <h3>${cfg.productName} for Developers</h3>

                <p>If coding is your thing, you can use ${cfg.productName} to
                host your open source development project.</p>

                <h4 class="helpHeader">What's a project?</h4>

                <p>It can be anything from packaging an
                app so it'll be available for use on Conary-based systems,
                to the creation of an operating system environment tailored
                for a specific purpose.</p>

                <h4 class="helpHeader">What do you get?</h4>

                <p>Here's the list:</p>

                <ul>

                    <li>A Conary repository dedicated to your project</li>

                    <li>A project-specific hostname
                    (&lt;project-name&gt;.rpath.org)</li>

                    <li>Project-specific mailing lists:

                            <li>&lt;project-name&gt;@rpath.org</li>

                            <li>&lt;project-name&gt;-commits@rpath.org</li>

                            <li>&lt;project-name&gt;-devel@rpath.org (if
                            desired)</li>

                            <li>&lt;project-name&gt;-bugs@rpath.org (if
                            desired)</li>

                        </li>

                        <li>A no-frills project-specific page
                        (http://&lt;project-name&gt;.rpath.org/ or http://${siteHost}${cfg.basePath}project/&lt;project-name&gt;/)</li>

                        <li>The ability to create "releases" (downloadable
                        ISO images) with a single mouse click</li>

                        <li>A project membership framework that allows you
                        to keep track of your project's members (people
                        able to commit changes to your project's
                        repository) and owners (people that can manage
                        project membership as well as having commit
                        access)</li>

                </ul>

                <h4 class="helpHeader">How much does it cost?</h4>

                <p>Nothing&#8212;${cfg.productName}'s services are free
                for any open source project.</p>

                <p>Not the project creating type?  If you see an
                interesting project, offer your services to the project's
                owners.  If they accept, they'll make you a member of the
                project, and you'll be able to start contributing
                immediately.</p>

                <h2>HOW DO I GET STARTED?</h2>

                <p>First, you need to create your own ${cfg.productName}
                account.</p>

                <p>To do this, click on the <a href="${cfg.basePath}register">new
                account</a> link at the top right-hand side of the
                ${cfg.productName} homepage.  You'll be taken to a form to
                fill out.  At a minimum you must fill in the following
                fields:</p>

                <ul>

                    <li><tt>Username</tt> &#8212; Limit to no more than 16
                    characters</li>

                    <li><tt>Email Address</tt> &#8212; This email address is
                    strictly for rPath to contact you regarding
                    ${cfg.productName}</li>

                    <li><tt>New Password</tt> &#8212; The password you'll
                    use to login to your account (must be at least 6
                    characters)</li>

                    <li><tt>Confirm Password</tt> &#8212; Confirmation of
                    the password you entered above.</li>

                </ul>

                <p>Even though it is not required, you should strongly
                consider filling in the <tt>Contact Information</tt> field.
                Why?  Well, if you are going to create a project, it's
                highly likely that people will have questions about the
                project, and they'll be using the contents of this field to
                contact you.  (Note that whatever you enter here will be
                publicly accessible, so you should use either a URL, or
                notation such as <tt>name at example dot com</tt> to make
                life more difficult for spammers.)</p>

                <p>Finally, you must check the two checkboxes entitled
                <tt>I have read and accept the Terms of Service</tt> and
                <tt>I have read and accept the Privacy Policy</tt>.</p>

                <p>Click on <tt>Register</tt>, and you will receive an
                email (sent to the email address you entered) with a
                confirmation link.  Use your browser to follow the link,
                and you'll then be able to login.</p>

                <h3>Creating a New Project</h3>

                <p>If you'd like to create a new project, start the project
                creation process by clicking on the <tt>Create a new
                project</tt> link.  After that, the process is no more
                complex than filling in a few text fields and clicking on a
                <tt>Create</tt> button.</p>

                <p>After that, creating a customized distribution can be as
                easy as <a
                href="http://wiki.conary.com/DerivativeDistroTutorial">this</a>!</p>

                <h3>Joining an Existing Project</h3>

                <p>If you're interested in joining an already-existing
                project, go to the project's homepage.  Click on the
                <tt>Request to join</tt> link at the bottom of
                the page, enter any comments you'd like to make to the
                project's owners, and click on <tt>Submit</tt>.  Your
                request will be forwarded to the project's owners, who can
                then review your request.</p>
            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
