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

    <head>
        <title>${formatTitle('Create Your Own Software Appliance')}</title>
    </head>

    <body>
        <div class="layout" id="helpPage">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="spanleft" class="devTutorial">
                <h1>Create Your Own Software Appliance</h1>
                <p>
                    rBuilder provides its users the tools necessary to build
                    and distribute their own Conary-based software appliances.
                    Use the following steps to create your own software appliance 
                    using existing packages in rBuilder.
                </p>

                <h2>1) Create a new group for your ${projectText().lower()}</h2>
                <p>
                    Your new group will represent the recipe for your software
                    appliance. From your ${projectText().lower()}'s home page, click Group Builder
                    and complete the form with the new group's details.
                </p>

                <h2>2) Add packages to your group</h2>
                <p>
                    Adding packages to a group is like adding ingredients for your recipe. 
                    Use the Search text box at the top of the rBuilder web interface to find 
                    packages you want to include, and click Add to group beside a package to 
                    choose it for your appliance. The Group Builder on the right side of the 
                    page will show the packages you have selected and provide links to use 
                    while you build your group recipe.
                </p>

                <h2>3) Cook your group</h2>
                <p>
                    After you have chosen the packages for your group, you are ready to cook. 
                    Click Cook this Group in the Group Builder and watch as rBuilder assembles 
                    the chosen packages in the group recipe. When the group is finished cooking, 
                    you can create and manage builds to distribute as your new software appliance.
                </p>

                <h2>4) Build the software appliance</h2>
                <p>
                    Create a build to make your cooked group into a distributable software appliance. 
                    Click Manage Builds, choose a cooked group and a build type (such as installable 
                    CD/DVD or VMware&reg; Player image), and create the new build. Then, click Manage 
                    Releases to publish one or more builds in a release, making them available for download.
                </p>

                <p>
                    For detailed instructions on these rBuilder operations and more, see the 
                    <a href="http://wiki.rpath.com/wiki/rBuilder?version=${constants.mintVersion}">rBuilder documentation at wiki.rpath.com</a>.
                </p>

                <p>To extend rBuilder functions, you might also choose to:</p>
                <ul>
                    <li><a href="http://wiki.rpath.com/wiki/Conary:Packager?version=${constants.mintVersion}">Create your own packages</a> for your ${projectText().lower()} on a local Conary-based system</li>
                    <li>Step through an introduction to packaging using the <a href="http://wiki.rpath.com/wiki/Conary:New_Package_Tutorial?version=${constants.mintVersion}">New Package Tutorial</a>, including the steps to package your own software for rBuilder Online</li>
                    <li><a href="http://wiki.rpath.com/wiki/Application-to-Appliance?version=${constants.mintVersion}">Make your application into an appliance</a> by incorporating rBuilder and other rPath technologies in the <a href="http://wiki.rpath.com/wiki/Appliance_Build_Instructions?version=${constants.mintVersion}">appliance build process</a></li>
                </ul>
            </div>
        </div>
    </body>
</html>
