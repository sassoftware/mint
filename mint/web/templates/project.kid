<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels, buildtypes
    from mint.client import timeDelta
    from mint.client import upstream
    from mint.helperfuncs import truncateForDisplay

    def condUpstream(upstreams, version):
        up = upstream(version)
        if upstreams[up] > 1:
            return version.trailingRevision().asString()
        else:
            return up
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

    <div py:def="projectResourcesMenu" id="project" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
            projectUrl = project.getUrl()
            projectAdmin = project.projectAdmin(auth.username)
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader">Project Resources</div>
        <ul>
            <li py:attrs="{'class': (lastchunk == '') and 'selectedItem' or None}"><a href="$projectUrl">Project Home</a></li>
            <li py:if="isWriter" py:attrs="{'class': (lastchunk in ('build', 'builds', 'newBuild', 'editBuild')) and 'selectedItem' or None}"><a href="${projectUrl}builds">Manage Builds</a></li>
            <li py:attrs="{'class': (lastchunk in ('release', 'releases', 'newRelease', 'editRelease', 'deleteRelease')) and 'selectedItem' or None}"><a href="${projectUrl}releases">${isOwner and 'Manage' or 'View'} Releases</a></li>
            <li py:attrs="{'class': (lastchunk == 'members') and 'selectedItem' or None}"><a href="${projectUrl}members">${isOwner and 'Manage' or 'View'} Project Membership</a></li>
            <li py:if="isWriter and not project.external" py:attrs="{'class': (lastchunk in ('groups', 'editGroup', 'editGroup2', 'newGroup', 'pickArch', 'cookGroup')) and 'selectedItem' or None}"><a href="${projectUrl}groups">Group Builder</a></li>
            <li py:attrs="{'class': (lastchunk in ('browse', 'troveInfo')) and 'selectedItem' or None}"><a href="${projectUrl}../../repos/${project.getHostname()}/browse">Browse Repository</a></li>
            <li py:if="projectAdmin" py:attrs="{'class': (lastchunk in ('userlist', 'addGroupForm', 'addPermForm', 'manageGroupForm')) and 'selectedItem' or None}"><a href="${projectUrl}../../repos/${project.getHostname()}/userlist">Manage Repository Permissions</a></li>
            <li py:if="cfg.EnableMailLists" py:attrs="{'class': (lastchunk == 'mailingLists') and 'selectedItem' or None}"><a href="${projectUrl}mailingLists">${isOwner and 'Manage' or 'View'} Mailing Lists</a></li>
            <li py:if="0" py:attrs="{'class': (lastchunk == 'bugs') and 'selectedItem' or None}"><a href="#">Bug Tracking</a></li>
            <li py:attrs="{'class': (lastchunk == 'help') and 'selectedItem' or None}"><a href="${projectUrl}help">Help</a></li>
        </ul>
    </div>

    <div py:def="releasesMenu(releases, isOwner=False, display='block')" py:strip="True">
        <?python
            projectUrl = project.getUrl()
        ?>
        <div py:if="releases" class="palette" id="releases">
            <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
            <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

            <div class="boxHeader">
                Recent Releases
                <a href="${projectUrl}rss">
                    <img class="noborder" alt="RSS"
                         style="margin-right:10px; vertical-align: middle;"
                         src="${cfg.staticPath}apps/mint/images/rss-inline.gif" />
                </a>
            </div>
            <div id="release_items" style="display: $display">
              <dl py:if="releases">
                <?python projectName = project.getName() ?>
                <div py:strip="True" py:for="release in releases[:5]">
                    <dt><a href="${projectUrl}release?id=${release.id}" title="${release.name} version ${release.version}">${truncateForDisplay(release.name, maxWords=5, maxWordLen=15)}</a></dt>
                    <dd>Version ${release.version}</dd>
                </div>
              </dl>
              <div py:if="not releases">
                 <dl><dt>No Releases</dt></dl>
              </div>
              <div class="release" py:if="isOwner" style="text-align: right; padding-right:8px;">
                  <a href="${projectUrl}newRelease"><strong>Create a new release</strong></a>
              </div>
              <div class="release" py:if="not isOwner and len(releases) > 5" style="text-align: right; padding-right:8px;">
                  <a href="${projectUrl}releases"><strong>More...</strong></a>
              </div>
            </div>
        </div>
    </div>

    <div py:def="commitsMenu(commits, display='block')" py:strip="True">
      <div py:if="commits" class="palette" id="commits">
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

        <div class="boxHeader">Recent Commits</div>
        <div id="commit_items" style="display: $display">
          <dl>
            <div py:strip="True" py:for="commit in commits">
                <dt><a href="${cfg.basePath}repos/${project.getHostname()}/troveInfo?t=${commit[0]};v=${commit[2]}">${truncateForDisplay(commit[0], maxWordLen=24)}</a></dt>
                <dd>${commit[1]} (${timeDelta(commit[3])})</dd>
            </div>
         </dl>
        </div>
      </div>
    </div>

    <div py:def="projectsPane()" id="projectsPane" >
        <script type="text/javascript">
        addLoadEvent(function() {
            var rMakeMimeType = navigator.mimeTypes["application/x-rmake"];
            if (rMakeMimeType) {
                var rMake = document.getElementById("rMake");
                if (rMake) {
                    swapDOM(rMake, DIV({id : "rMake"},
                                       A({href : BaseUrl + 'rMake?supported=1',
                                          style: 'font-weight: bold;'},
                                         'rMake')));
                }
            }
            });
        </script>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_orange_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_orange_right.png" alt="" />
        <div class="boxHeader">
            <div class="boxHeaderText">
                <span>${auth.username}</span>
                <a class="signout" href="http://${cfg.siteHost}${cfg.basePath}logout">
                    Sign Out
                </a>
            </div>
        </div>
        <div class="boxBody" py:if="not projectList">
            <h3>Get Involved</h3>

            <p>Now's the time to get involved with the ${cfg.productName}
            community. There are several ways you can do this:</p>

            <ul>
                <li>You can <a
                href="http://${SITE}newProject"><strong>create a new
                project</strong></a>.</li>

                <li>You can join an existing project.</li>
            </ul>

            <p>To join an existing project, use the browse or search boxes
            in header to find a project that interests you.
            Then, click on the project name, and click on the "Request to join"
            link to submit your request to the project's owners.</p>
            <div id="userSettings"><a href="http://${SITE}userSettings"><strong>Edit my account</strong></a></div>
	    <div id="administer" py:if="auth.admin"><a href="http://${SITE}admin/"><strong>Site administration</strong></a></div>
        </div>
        <div class="boxBody" id="boxBody" py:if="projectList">
            <div py:for="level, title in [(userlevels.OWNER, 'Projects I Own'),
                                          (userlevels.DEVELOPER, 'Projects I Work On'),
                                          (userlevels.USER, 'Projects I Am Watching')]"
                 py:strip="True">
                <div py:strip="True" py:if="level in projectDict">
                    <h4>${title}</h4>
                    <ul>
                        <li py:for="project in sorted(projectDict[level], key = lambda x: x.name)">
                            <a href="${project.getUrl()}">
                                ${project.getNameForDisplay()}</a>
                                <span py:if="not level and project.listJoinRequests()">
                                    <a href="${project.getUrl()}members"><b style="color: red;">Requests Pending</b></a>
                                </span>
                        </li>
                    </ul>
                </div>
            </div>
            <div id="newProject" py:if="auth.admin or not cfg.adminNewProjects"><a href="http://${SITE}newProject"><strong>Create a new project</strong></a></div>
            <div id="userSettings"><a href="http://${SITE}userSettings"><strong>Edit my account</strong></a></div>
            <div id="administer" py:if="auth.admin"><a href="http://${SITE}admin/"><strong>Site administration</strong></a></div>
            <div id="rMake"><a href="http://${SITE}rMake/" style="font-weight: bold;">rMake</a></div>
        </div>
    </div>

    <div py:strip="True" py:def="buildTable(builds)">
        <table>
            <tr>
                <th>Build Name</th>
                <th>Arch</th>
                <th>Image Type</th>
            </tr>
            <div py:strip="True" py:for="build in builds">
                ${buildTableRow(build)}
            </div>
        </table>
    </div>

    <div py:strip="True" py:def="buildTableRow(build)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            from mint.web.templatesupport import downloadTracker
            shorterName = truncateForDisplay(build.name)
            buildFiles = build.getFiles()
        ?>
        <tr class="buildHeader">
            <td><a href="${basePath}build?id=${build.id}">${shorterName}</a></td>
            <td>${build.getArch()}</td>
            <td>${buildtypes.typeNamesShort[build.buildType]}</td>
        </tr>
        <tr>
            <td colspan="3">
                <ul class="downloadList">
                    <li py:for="i, file in enumerate(buildFiles)">
                        <?py fileUrl = cfg.basePath + "downloadImage/" + str(file['fileId']) + "/" + file['filename'] ?>
                        <a py:attrs="downloadTracker(cfg, fileUrl)" href="http://${cfg.siteHost}${fileUrl}">${file['title'] and file['title'] or "Disc " + str(i+1)}</a> (${file['size']/1048576}&nbsp;MB)
                    </li>
                    <li py:if="not buildFiles">Build contains no downloadable files.</li>
                </ul>
            </td>
        </tr>
    </div>
</html>
