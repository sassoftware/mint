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
                var steps = Array('none', 'step1', 'step2', 'step3', 'step4');
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
                <h1>rBuilder Online for Users</h1>

                <p>If you are already using a Conary-based system, then you have come to the
                    right place to look for software.</p>

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


                <h2><a href="javascript:showStep(1);">Step 1. Find the right package or distribution</a></h2>
                <div py:attrs="attrs[1]" id="step1">
                    <p>Browse the repository or search for the right package.</p>
                    <div class="helpBlock">
                        <p>Use the Browse and Search boxes on the left hand side to find the projects 
                        or packages that suits your needs. If you are looking for a complete distribution, 
                        look for the Recent Releases box on the left side of a project's home page.</p>
                    </div>
                </div>

                <h2><a href="javascript:showStep(2);">Step 2. Download and Install</a></h2>
                <div py:attrs="attrs[2]" id="step2">
                    <p>It is quick and easy, whether a installing package or a whole distribution.</p>

                    <div class="helpBlock">
                        <p>If you just want to install a package, then you should type, as root:</p>

                        <pre>[user@host ~]# <b>conary update &lt;package&gt;=&lt;project label&gt;</b>

</pre>

                        <p>You can get the <tt>&lt;project label&gt;</tt> from the "Install packages 
                            from this project" link on the project's home page.</p>

                        <p>If you want to install a complete distribution, then select one of the Recent 
                        Releases on the left hand side of the home page.  Download the ISO image, 
                        burn it to a CD, and use it to install your system.</p>
                    </div>
                </div>

                <h2><a href="javascript:showStep(3);">Step 3. Stay Up To Date</a></h2>
                <div py:attrs="attrs[3]" id="step3">
                    <p>Of course you can keep the software updated, but you can also keep track of
                        what is going on with the project.</p>

                    <div class="helpBlock"> 
                        
                        <p>To keep the software updated, you only need to run, as root:</p>
                        <pre>[user@host ~]# <b>conary update &lt;package&gt;</b>

</pre>
                        <p>or</p>
                        <pre>[user@host ~]# <b>conary updateall</b>

</pre>
                        
                        <p>to get the newest version&#x2014;no need to go looking.  Even if you have 
                            installed software from several different projects, conary keeps track of
                            packages and where they came from and gets you the updates.</p>

                        <p>Interested in a particular project?  There are several ways you can follow a
                            project:</p>

                        <ul>
                            <li>Click "Watch this project" on the project's home page and you will get 
                                a quick link to the project's home page in your "My Projects" area.</li>
                            <li>Subscribe to the project's RSS feed for release news.</li>
                            <li>Follow the developer discussions and code commits using the project's 
                                mailing lists.</li>
                        </ul>
                    </div>
                </div>


                
                <h2><a href="javascript:showStep(4);">Step 4. Participate in a project or create your own project</a></h2>

                <div py:attrs="attrs[4]" id="step4">
                    <p>Join up with others or strike out on your own.</p>

                    <div class="helpBlock">

                        <p>If you want to help in the development of a project, simply request to join a 
                        project from the project's home page.  But you do not have to be a coder to 
                        participate.  All projects need people to help out with testing, 
                        documentation, design, etc.  If there is an interesting project, feel free to 
                        create an rBuilder Online account, and offer your services.</p>

                        <p>If you would like to start your own project, then get started here: 
                            <a href="/help?page=dev-tutorial">rBuilder Online for Developers</a></p>

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
