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
        <a href="help">Help</a>
        <a href="#">Feedback</a>
    </div>

    <head>
        <title>${formatTitle('Help: Feedback')}</title>
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
                <h3>Need Help? Have Feedback?</h3>

                <p>${cfg.productName} is a work in progress, so if you need help or have any
                feedback, we'd love to hear from you!</p>

                <p>You can reach us two ways:</p>

                <h3>IRC</h3>

                <p>To chat online with the ${cfg.productName} developers, join the IRC channel
                #conary on the <a href="http://www.freenode.net/">Freenode IRC network</a>.</p>

                <p>(Note that, although we often work long hours, we do sleep occasionally, so
                if you don't get a response on IRC, try again later, or send us email.)</p>

                <h3>EMAIL</h3>

                <p>To contact the ${cfg.productName} developers via email, send your mail to
                <a href="mailto:rbuilder@rpath.com">rbuilder@rpath.com</a> and we'll get
                back to you as soon as we can.</p>
            </div>
        </td>
        <td id="right" class="projects">
        </td>
    </body>
</html>
