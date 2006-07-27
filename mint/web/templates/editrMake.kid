<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.rmakeconstants import buildjob
?>
    <head>
        <title>${formatTitle('Edit rMake build')}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="spanleft" py:if="not rMakeBuild.status">
                <h1>Edit rMake build</h1>
                <form method="post" action="editrMake2">
                    Title:
                    <input type="text" name="title" value="${rMakeBuild.title}" size="16" maxlength="128"/>
                    <p><button class="img" type="submit">
                        <img src="${cfg.staticPath}/apps/mint/images/apply_changes_button.png" alt="Apply Changes" />
                    </button></p>
                </form>
                <p>
                    <button class="img" onclick="javascript:window.location='commandrMake?command=build';" type="button">
                        <img src="${cfg.staticPath}/apps/mint/images/build_rmake_button.png" alt="Build" />
                    </button>
                    <button class="img" onclick="javascript:window.location='deleterMakeBuild';" type="button">
                        <img src="${cfg.staticPath}/apps/mint/images/delete_button.png" alt="Delete rMake build" />
                    </button>
                </p>
                <h3 style="color:#FF7001;">Step 1: Add Packages To Your rMake build</h3>
                <p>You now have an rMake build. Add packages to the build from
                any ${cfg.productName} project that lists you as a member. To
                add a package, search or browse for the desired package and
                click on its "Add to ${rMakeBuild.title}" link.</p>

                <h3 style="color:#FF7001;">Step 2: Build Your rMake build</h3>
                <p>Once all the desired packages have been added to the build,
                click on the "Build" button. rMake will then assign the build
                a job ID, retrieve the packages, build them on your system, and
                display a dynamically-updated status page.</p>

                <h3 style="color:#ff7001;">Step 3: Commit</h3>
                <p>Once your rMake job has successfully built, click on the
                "Commit" button to copy the newly-built software back to the
                originating repositories.
                </p>
            </div>
            <div id="spanleft" py:if="rMakeBuild.status">
                <h3>This rMake build cannot be edited because it is currently being processed.</h3>
                <div><a href="${cfg.basePath}rMakeStatus">View Status</a></div>
                <p><strong>Possible Operations:</strong></p>
                <div><a href="${cfg.basePath}resetrMakeStatus?referer=${selfLink}">Reset rMake Status</a></div>
                <div py:if="rMakeBuild.status not in (buildjob.JOB_STATE_FAILED, buildjob.JOB_STATE_BUILT, buildjob.JOB_STATE_INIT)"><a href="${cfg.basePath}commandrMake?command=stop">Stop rMake build</a></div>
                <div py:if="rMakeBuild.status == buildjob.JOB_STATE_BUILT"><a href="${cfg.basePath}commandrMake?command=commit">Commit rMake build</a></div>
            </div>
        </div>
    </body>
</html>
