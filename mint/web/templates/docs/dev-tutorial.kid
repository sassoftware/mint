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

    <head>
        <title>${formatTitle('Create Your Own Software Appliance')}</title>
    </head>

    <body>
        <div class="layout" id="helpPage">
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="spanleft" class="devTutorial">
                <h1>Create Your Own Software Appliance</h1>
                <p py:if="not auth.authorized">
                    If you already have an ${cfg.productName} account, please log in now. If
                    you don't already have an ${cfg.productName} account, you will need to
                    <strong><a href="http://${SITE}register">create one</a></strong>.
                </p>

                <p py:if="auth.authorized and not ownsProjects">
                    You will need your own project in order to build a software appliance.
                    Get started by <strong><a href="http://${SITE}newProject">creating a new
                    project</a></strong>.
                </p>


                <div py:if="ownsProjects" py:omit="True">
                    <p>
                        This tutorial steps you through the process of creating your own
                        software appliance from packages that already exist on rBuilder
                        Online.  If you would like to build and contribute your own packages,
                        you should follow the <strong><a href="http://wiki.conary.com/DerivativeDistroTutorial?action=AttachFile;do=get;target=rBuilderOnlineTutorial.pdf">steps to
                        building packages with rBuilder Online</a></strong>.
                    </p>

                    <h2>Step 1. First, create a new group</h2>

                    <p>
                        <img src="${cfg.staticPath}apps/mint/images/mag_glass.png" alt="Magnifying Glass" />
                        Your new group will hold the recipe for your software appliance.  From
                        your project's home page, click on "Group Builder" and fill in your
                        group's details.
                    </p>

                    <h2 style="clear: left;">Step 2. Next, add the packages you want</h2>

                    <p>
                        <img src="${cfg.staticPath}apps/mint/images/ingredients.png" alt="ingredients" />
                        Now it's time to add in the ingredients for your software appliance.
                        Using the Search box, find the packages you want to include and click
                        "Add to group." Each time, you will see the package you selected
                        appear in the Group Builder sidebar.
                    </p>

                    <h2 style="clear: left;">Step 3. Finally, build your software appliance</h2>

                    <p>
                        <img src="${cfg.staticPath}apps/mint/images/pot.png" alt="Cooking Pot" />
                        The last step is to "cook" your software appliance.  Click "Cook this
                        Group" and watch as rBuilder Online assembles the packages you chose
                        into a complete system.  When the group is "Finished" cooking, you can
                        go to the releases page to publish and share your work.
                    </p>
                </div>
            </div>
        </div>
    </body>
</html>
