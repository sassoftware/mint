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
        <a href="${cfg.basePath}help">Help</a>
        <a href="#">Developers</a>
    </div>

    <head>
        <title>${formatTitle('Help: Developers')}</title>
        <script>
            <![CDATA[
                var curStep = ${step};
                var steps = Array('none', 'step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8');
                function showStep(step) {
                    for(var i = 1; i < steps.length; i++ ) {
                        stepEl = document.getElementById(steps[i]);
                        if(!stepEl)
                            alert(i + " - " + steps[i] + " - " + stepEl);
                        stepEl.style.display = "none";
                    }
                    stepEl = document.getElementById(steps[step]);
                    stepEl.style.display = "block";
                    if(step == 1) {
                        document.getElementById("prevImg1").style.visibility = "hidden";
                        document.getElementById("nextImg1").style.visibility = "visible";
                        document.getElementById("prevImg2").style.visibility = "hidden";
                        document.getElementById("nextImg2").style.visibility = "visible";
                    } else if(step == 8) {
                        document.getElementById("prevImg1").style.visibility = "visible";
                        document.getElementById("nextImg1").style.visibility = "hidden";
                        document.getElementById("prevImg2").style.visibility = "visible";
                        document.getElementById("nextImg2").style.visibility = "hidden";
                    } else {
                        document.getElementById("prevImg1").style.visibility = "visible";
                        document.getElementById("nextImg1").style.visibility = "visible";
                        document.getElementById("prevImg2").style.visibility = "visible";
                        document.getElementById("nextImg2").style.visibility = "visible";
                    }
                    document.getElementById("showAll2").style.visibility = "visible";

                    curStep = step;
                }
                function showAll() {
                    for(var i = 1; i < steps.length; i++ )
                        document.getElementById(steps[i]).style.display = "block";
                    document.getElementById("prevImg1").style.visibility = "hidden";
                    document.getElementById("nextImg1").style.visibility = "hidden";
                    document.getElementById("prevImg2").style.visibility = "hidden";
                    document.getElementById("nextImg2").style.visibility = "hidden";
                    document.getElementById("showAll2").style.visibility = "hidden";
                }

            ]]>
        </script>
    </head>

    <body onload="javascript:showStep(curStep);">
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>
        <?python
            attrs = dict([(i, {'style': i == step and "display: block;" or "display: none;"}) for i in range(1, 9)])
    ?>

        <td id="main">
            <div class="pad">

                <a href="xxx" style="float: right;">PDF of this document
                    <img style="border: none;" src="${cfg.staticPath}/apps/mint/images/pdficon_small.gif" />
                </a>

                <h1>rBuilder Online for Developers</h1>

                <p>You can create and publish your own packages or a complete distribution by
                following these simple steps:</p>

                <table style="width: 100%;">
                    <tr>
                        <td id="prevImg1" style="text-align: left; width: 50%;">
                            <img src="${cfg.staticPath}/apps/mint/images/prev.gif" /> 
                            <a href="javascript:showStep(curStep-1);">Previous Step</a>
                        </td>
                        <td id="nextImg1" style="text-align: right; width: 50%;">
                            <a href="javascript:showStep(curStep+1);">Next Step 
                            <img border="0" src="${cfg.staticPath}/apps/mint/images/next.gif" /></a>
                        </td>
                    </tr>
                </table>



                <h2><a href="javascript:showStep(1);">Step 1. Create an rBuilder Online account</a></h2>
                <div py:attrs="attrs[1]" id="step1">

                    <p>Anyone can search and download from rBuilder Online, but if you want to do
                    development on a package or create a distribution, you will need to <a href="/register">create
                    an account</a>.</p>

                    <div class="helpBlock">
                        <p>By clicking on the new account link above, you will be taken to a form where 
                        you will be asked to provide:</p>
                        <ul>
                          <li>Username</li>
                          <li>Password</li>
                          <li>Email Address</li>
                          <li>Information About You</li>
                        </ul>
                        <p>Even though it is not required, you should provide as much Contact Information 
                        as possible so that people who you collaborate with on projects may contact you.</p>
                    </div>
                </div>

                <h2><a href="javascript:showStep(2);">Step 2. Create a project or join an existing project</a></h2>
                <div py:attrs="attrs[2]" id="step2">
                    <p>What is a project? It can be anything from a single application to a
                    complete operating system.</p>

                    <div class="helpBlock">
                        <p>If you want to create your own project, follow the
                           <a href="http://www.rpath.com/newProject">New Project</a> link
                            and you will be taken to a form where you will be asked to provide:
                        </p>
                        
                        <ul>
                            <li>Project Name</li>
                            <li>Project Title and Description</li>
                            <li>External Project Page</li>
                            <li>Mailing Lists</li>
                        </ul>
                    </div>
                </div>

                <h2><a href="javascript:showStep(3);">Step 3. Install a Conary-based Linux distribution</a></h2>
                <div py:attrs="attrs[3]" id="step3">
                    <p>A good choice is rPath Linux, but there are many others available to choose from.</p>

                    <div class="helpBlock"> 
                        <p>You can use the most recent <a href="http://www.rpath.com/project/rpath/releases">rPath Linux</a> release.
                        Or to find other suitable Linux distributions, use the Browse Projects or 
                        Search box on the left hand side of your browser window.</p>
                    </div>
                </div>


                
                <h2><a href="javascript:showStep(4);">Step 4. Set up your build environment</a></h2>

                <div py:attrs="attrs[4]" id="step4">
                    <p>In order to build and contribute packages, you will need to setup a build
                    environment on your local machine.</p>

                    <div class="helpBlock">
                        <p>You will need to create the following directories on your local machine:</p>
                
                        <pre>[user@host ~]$ <b>mkdir ~/conary</b>
[user@host ~]$ <b>mkdir ~/conary/&lt;projectname&gt;</b>
[user@host ~]$ <b>mkdir ~/conary/&lt;projectname&gt;/builds</b>
[user@host ~]$ <b>mkdir ~/conary/&lt;projectname&gt;/cache</b>
[user@host ~]$ <b>mkdir ~/conary/&lt;projectname&gt;/src</b>

</pre>

                        <p>In addition, you will need to set up a local <tt>conaryrc</tt> file on 
                        your system for this project.  The local <tt>conaryrc</tt> file should 
                        contain the following:</p>

                        <pre>repositoryMap      &lt;projectname&gt;.rpath.org http://&lt;username:password&gt;@&lt;projectname&gt;.rpath.org/conary/
installLabelPath   &lt;projectname&gt;.rpath.org@rpl:devel
buildLabel         &lt;projectname&gt;.rpath.org@rpl:devel
buildPath          ~/conary/&lt;projectname&gt;/builds
lookaside          ~/conary/&lt;projectname&gt;/cache
contact            &lt;your email address&gt;
name               &lt;your full name&gt;

</pre>

                        <p>Put this conaryrc file in <tt>~/conary/projectname/</tt> and any time you use
                        Conary from that directory, it will override any settings such as buildLabel specified
                        in your main <tt>.conaryrc</tt> file in your home directory.</p>
                    </div>
                </div>
                

                <h2><a href="javascript:showStep(5);">Step 5. Create your recipe</a></h2>
                <div py:attrs="attrs[5]" id="step5">
                    <p>A recipe controls how a package is built or how an entire distribution is
                    put together.</p>

                    <div class="helpBlock">
                        <p>From the project source directory on your local system, create a new package:</p>

                        <p>Text in <b>bold</b> are the commands that you type.</p>
                        <pre>[user@host src]$ <b>cvc newpkg &lt;package&gt;</b>

</pre>
                        <p>A package directory will be created.  Change into that
                        package directory and create the package recipe:</p>

                        <pre>[user@host src]$ <b>cd &lt;package&gt;</b>
[user@host package]$ <b>gedit &lt;package&gt;.recipe</b>

</pre>
                        <p>To begin building your recipe, you may look at the 
                            <a href="http://wiki.conary.com/ConaryRecipe">documentation</a>.
                            It is often best to start developing your recipe by looking at 
                            existing recipes.  A good place to start is this 
                            <a href="http://wiki.conary.com/GroupSampleRecipePage">sample recipe</a>.
                            There are also a myriad of recipes in existing projects.
                            Browse the rPath Linux project repository for some good examples.
                        </p>
                    </div>
                </div>


                <h2><a href="javascript:showStep(6);">Step 6. Cook your recipe</a></h2>
                <div py:attrs="attrs[6]" id="step6">
                    <p>What else would you do with a recipe?  This is how you test that your
                    recipe will build your project properly.</p>
                
                    <div class="helpBlock">
                        <p>From the package directory on your local system, execute the following command:</p>

                        <pre>[user@host &lt;package&gt;]$ <b>cvc cook &lt;package&gt;.recipe</b>

</pre>

                        <p>If everything builds correctly, the results will be saved in a local 
                        changeset that you can view:</p>

                        <pre>[user@host &lt;package&gt;]$ <b>conary showcs --all &lt;package&gt;-&lt;version&gt;.ccs</b></pre>
                    </div>
                </div>


                <h2><a href="javascript:showStep(7);">Step 7. Check your recipe into the repository</a></h2>
                <div py:attrs="attrs[7]" id="step7">
                    <p>Now that you have verified that your recipe was cooked correctly, you will
                    want to check it into the repository.</p>

                    <div class="helpBlock">
                        <p>Just like most source code management systems, you will need to commit your 
                        work into the repository.  To commit your recipe into the repository, use the 
                        following command:</p>

                        <pre>[user@host &lt;package&gt;]$ <b>cvc add &lt;projectname&gt;.recipe</b>
[user@host &lt;package&gt;]$ <b>cvc commit --message "new recipe"</b>

</pre>

                        <p>Now you need to cook your package into the repository:</p>

                        <pre>[user@host &lt;package&gt;]$ <b>cvc cook &lt;package&gt;</b>

</pre>

                        <p>This final command will pull the recipe from the repository, build it on your 
                        local system, and check the resulting changeset back into the repository.</p>
                    </div>
                </div>


                <h2><a href="javascript:showStep(8);">Step 8. Publish your results</a></h2>
                <div py:attrs="attrs[8]" id="step8">

                    <p>Share what you have created with everyone else.</p>

                    <div class="helpBlock"> 
                        <p>For this step, you will need to go back to the project home page on rpath.org
                        (e.g., &lt;projectname&gt;.rpath.org)
                        If your recipe was written to contruct an entire distribution, you will want 
                        to create a release.  To do so, select releases from the left side menus.  
                        This will take you to a page where you can select your recipe and have it 
                        create fully installable images.  Publish the images and other rBuilder 
                        Online users will be able to download and install your distribution.</p>

                        <p>If your recipe was written to build a single package, then you will see that 
                        package has a cooked version in the repository.  Other rBuilder Online users 
                        will now be able to download and install your package, as well as shadow it 
                        for inclusion in their projects.</p>
                    </div>
                </div>


                <table style="width: 100%; padding: 0.5em; border-top: 2px solid gray;">
                    <tr>
                        <td id="prevImg2" style="text-align: left; width: 33%;">
                            <img src="${cfg.staticPath}/apps/mint/images/prev.gif" /> 
                            <a href="javascript:showStep(curStep-1);">Previous Step</a>
                        </td>
                        <td id="showAll2" style="text-align: center; width: 33%;">
                            <a href="javascript:showAll();">Show All</a>
                        </td>
                        <td id="nextImg2" style="text-align: right; width: 33%;">
                            <a href="javascript:showStep(curStep+1);">Next Step 
                            <img border="0" src="${cfg.staticPath}/apps/mint/images/next.gif" /></a>
                        </td>
                    </tr>
                </table>
                <p />
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
