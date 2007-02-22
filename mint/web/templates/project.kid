<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint import userlevels, buildtypes
    from mint.client import timeDelta
    from mint.client import upstream
    from mint.helperfuncs import truncateForDisplay
    from mint import urltypes
    from mint.builds import getExtraFlags

    def condUpstream(upstreams, version):
        up = upstream(version)
        if upstreams[up] > 1:
            return version.trailingRevision().asString()
        else:
            return up

    icons = {
        buildtypes.VMWARE_IMAGE: ("get-vmware-player.png", "http://www.vmware.com/download/player/", "Download VMware Player"),
        buildtypes.RAW_HD_IMAGE: ("get-parallels.png", "http://www.parallels.com/", "Try Parallels Workstation 2.2"),
        buildtypes.VIRTUAL_IRON: ("get-virtual-iron.png", "http://www.virtualiron.com/free", "Virtual Iron: Download Now"),
    }

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
            <li py:if="isWriter"><a href="${projectUrl}downloads">Download Statistics</a></li>
            <li><a href="http://wiki.rpath.com/wiki/Conary:Install_Config">Help</a></li>
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
        <?python
            from mint import rmakeconstants
        ?>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rmakebuilder.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript">
        <![CDATA[
        addLoadEvent(function() {
            supportedrMakeVersions = ${str(list(rmakeconstants.supportedApiVersions))};
            var rMakeVersion = rMakeProtocolVersion();
            if (rMakeVersion != 0) {
                var rMake = document.getElementById("rMake");
                if (rMake) {
                    swapDOM(rMake, DIV({id : "rMake"},
                                       A({href : BaseUrl + 'rMake?supported=' + rMakeVersion, style: 'font-weight: bold;'}, 'rMake')));
                }
            }
            });
        ]]>
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
            <h3>Get Started</h3>

            <p>Participate in the ${cfg.productName} community by:</p>

            <ul>
                <li><a
                href="http://${SITE}newProject"><strong>Creating a new
                project</strong></a></li>

                <li>Joining an existing project</li>
            </ul>

            <p>To join an existing project, use the "Browse projects" link or "Search" text box at the top of the page to find a project of interest. Then, submit your request to project owners: click a project name, click "View Project Membership" on the project panel at the left, and click "Request to join this project."</p>
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

    <div py:strip="True" py:def="buildTable(buildList)">
        <table>
            <div py:strip="True" py:for="build in buildList">
                ${buildTableRow(build)}
            </div>
        </table>
    </div>

    <div py:strip="True" py:def="buildTableRow(build)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            shorterName = truncateForDisplay(build.name)
        ?>
        <tr style="background: #f0f0f0; font-weight: bold;" class="buildHeader">
            <td><a href="${basePath}build?id=${build.id}">${shorterName}</a></td>
            <td style="text-align: center;">${build.getArch()}
            &nbsp;${buildtypes.typeNamesMarketing[build.buildType]}</td>
        </tr>
        ${buildFiles(build)}
        <tr><td colspan="2" class="buildTypeIcon">${getBuildIcon(build)}</td></tr>
    </div>

    <div py:strip="True" py:def="getBuildIcon(build)">
        <a py:if="build.buildType in icons" title="${icons[build.buildType][2]}" href="${icons[build.buildType][1]}">
            <img class="buildTypeIcon" src="${cfg.staticPath}apps/mint/images/${icons[build.buildType][0]}" alt="${icons[build.buildType][2]}" />
        </a>
    </div>

    <div py:strip="True" py:def="buildFiles(build)">
        <?python
            from mint.web.templatesupport import downloadTracker
            extraFlags = getExtraFlags(build.troveFlavor)
        ?>
        <tr py:for="f in build.getFiles()">
            <td style="border-bottom: 1px solid #e6e6e6;">
                <?python
                    title = f['title'] or ("Disc %d" % (f['idx'], ))
                    size = f['size'] or 0
                    sha1 = f['sha1'] or ''
                ?>
                <span style="font-weight: bold;">${title}</span>
                <div style="font-size: smaller;" py:if="extraFlags">${extraFlags}</div>
                <div style="font-size: smaller;" py:if="size">${size/1048576} MB<span py:if="self.cfg.displaySha1 and sha1">, SHA1: ${sha1}</span></div>
            </td>
            <td style="text-align: right; vertical-align: top; border-bottom: 1px solid #e6e6e6;">
                <?python
                    filteredFileUrls = [ x for x in f['fileUrls'] if x[1] in self.cfg.visibleUrlTypes or x[1] == urltypes.LOCAL ]
                    urlTypeList = [ x[1] for x in filteredFileUrls ]
                ?>
                <img src="/conary-static/apps/mint/images/download-icon.png" style="float: right;"/>
                <div py:strip="True" py:for="urlId, urlType, url in filteredFileUrls">
                    <span py:if="not (urlType == urltypes.LOCAL and self.cfg.redirectUrlType in urlTypeList)" style="vertical-align: top; font-size: smaller;">
                        <?python
                        fileUrl = cfg.basePath + 'downloadImage?fileId=%d%s' % (f['fileId'], (urlType not in (urltypes.LOCAL, self.cfg.redirectUrlType)) and ('&urlType=%d' % urlType) or '')
                        ?>
                        <a py:attrs="downloadTracker(cfg, fileUrl)" href="${fileUrl}">${urltypes.displayNames[urlType]}</a><br />
                    </span>
                </div>
            </td>
        </tr>
    </div>

    <div py:def="downloadsMenu(builds, display='block')" py:omit="True">
      <div py:if="builds" class="downloadPalette" id="release">
        <div class="boxHeader">Download NOW</div>
        <div style="display: $display;">
            <ul style="list-style-type: none;">
                <div py:for="build in builds">
                    <?python
                        # fetch the first file and the first URL we have for a build
                        file = build.getFiles()[0]
                        title = file['title'] or ("Disc %d" % (file['idx'], ))
                        fileUrl = cfg.basePath + 'downloadImage?fileId=%d' % file['fileId']
                        extraFlags = getExtraFlags(build.troveFlavor)
                    ?>
                    <li>
                        <a href="$fileUrl">${build.getArch()} ${buildtypes.typeNamesMarketing[build.buildType]}</a>
                        <span py:omit="True" py:if="extraFlags">(${", ".join(extraFlags)})</span>
                    </li>
                </div>
            </ul>

            <span style="float: right;"><a href="http://wiki.rpath.com/wiki/rBuilder:Build_Types" target="_blank"><b>Which one do I want?</b></a></span>
            <span><a href="${project.hostname}/latestRelease"><b>More Information...</b></a></span>
        </div>
      </div>
    </div>


</html>
