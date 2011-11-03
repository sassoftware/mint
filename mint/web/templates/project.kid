<?xml version='1.0' encoding='UTF-8'?>
<?python
    #
    # Copyright (c) 2005-2008 rPath, Inc.
    # All Rights Reserved
    #
    from mint.web.templatesupport import projectText
    from mint import userlevels, buildtypes, constants
    from mint.client import timeDelta
    from mint.client import upstream
    from mint.helperfuncs import truncateForDisplay, formatProductVersion
    from mint import urltypes
    from mint.builds import getExtraFlags
    from mint.config import isRBO

    def condUpstream(upstreams, version):
        up = upstream(version)
        if upstreams[up] > 1:
            return version.trailingRevision().asString()
        else:
            return up


?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

    <div py:def="productVersionMenu(readOnly=False)" py:strip="True">
        <div py:if="auth.authorized and self.isWriter" id="productVersion">
            <span py:if="readOnly and versions" py:strip="True">Version: ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</span>
            <span py:if="not readOnly and versions" py:strip="True">${versionSelection(versions, True, currentVersion)}</span>
            <span py:if="not versions" py:strip="True">No versions available</span>
        </div>
    </div>

    <div py:def="projectResourcesMenu(readOnlyVersion=False)" id="project" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
            projectUrl = project.getUrl(baseUrl)
            projectAdmin = project.projectAdmin(auth.username)
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader"><span class="bracket">[</span> ${projectText().title()} Resources <span class="bracket">]</span></div>
        <ul class="navigation">
            <li py:attrs="{'class': (lastchunk == '') and 'selectedItem' or None}"><a href="$projectUrl">${projectText().title()} Home</a></li>
            <li py:if="isWriter" py:attrs="{'class': (lastchunk in ('newPackage', 'newUpload', 'maintainPackageInterview', 'getPackageFactories', 'savePackage')) and 'selectedItem' or None}"><a href="${projectUrl}newPackage">Create Package</a></li>
            <li py:if="isOwner and versions and currentVersion and project.isAppliance" py:attrs="{'class': (lastchunk in ('landing',)) and 'selectedItem' or None}"><a href="${cfg.basePath}apc/${project.shortname}/">Manage Appliance</a></li>
            <li py:attrs="{'class': (lastchunk in ('build', 'builds', 'newBuild', 'editBuild')) and 'selectedItem' or None}"><a href="${projectUrl}builds">${isOwner and 'Manage' or 'View'} Images</a></li>
            <li py:attrs="{'class': (lastchunk in ('release', 'releases', 'newRelease', 'editRelease', 'deleteRelease')) and 'selectedItem' or None}"><a href="${projectUrl}releases">${isOwner and 'Manage' or 'View'} Releases</a></li>
            <li py:attrs="{'class': (lastchunk == 'members') and 'selectedItem' or None}"><a href="${projectUrl}members">${isOwner and 'Manage' or 'View'} ${projectText().title()} Membership</a></li>
            <li py:attrs="{'class': (lastchunk in ('browse', 'troveInfo')) and 'selectedItem' or None}"><a href="${projectUrl}../../repos/${project.getHostname()}/browse">Browse Repository</a></li>
            <li py:if="projectAdmin and cfg.rBuilderOnline" py:attrs="{'class': (lastchunk in ('userlist', 'addGroupForm', 'addPermForm', 'manageGroupForm')) and 'selectedItem' or None}"><a href="${projectUrl}../../repos/${project.getHostname()}/userlist">Manage Repository Permissions</a></li>
            <li py:if="0" py:attrs="{'class': (lastchunk == 'bugs') and 'selectedItem' or None}"><a href="#">Bug Tracking</a></li>
            <li py:if="isWriter and cfg.rBuilderOnline" py:attrs="{'class': (lastchunk == 'downloads') and 'selectedItem' or None}"><a href="${projectUrl}downloads">Download Statistics</a></li>
        </ul>
    </div>

    <div py:def="versionSelection(versions, unselected=False, currentVersion=None)" py:strip="True">
        <?python
            v = set([x[2] for x in versions])
            showNamespace = len(v) > 1
        ?>
        <form id="versionSelectorForm" action="${basePath}setProductVersion" method="POST">
            <label for="productVersionSelectorDropdown">Version:</label>
            <select name="versionId" id="productVersionSelectorDropdown">
                <option py:if="unselected" value="-1" py:attrs="{'selected': (unselected and not currentVersion) and 'selected' or None}">Not Selected</option>
                <option py:for="ver in versions" value="${ver[0]}" py:attrs="{'selected': (ver[0] == currentVersion) and 'selected' or None}">
                    <div py:strip="True" py:if="showNamespace">${ver[3]} (${ver[2]})</div>
                    <div py:strip="True" py:if="not showNamespace">${ver[3]}</div>
                </option>
            </select>
            <input id="product_version_redirect" type="hidden" name="redirect_to" value=""/>
        </form>
        <script type="text/javascript">
            jQuery('#productVersionSelectorDropdown').change(function() {
                jQuery('#versionSelectorForm').submit();
            });
            jQuery(document.body).ready(function() {
                jQuery('#product_version_redirect').val(document.location);
            });
        </script>
    </div>

    <div py:def="releasesMenu(releases, isOwner=False, display='block')" py:strip="True">
        <?python
            projectUrl = project.getUrl(baseUrl)
        ?>
        <div py:if="releases" class="palette" id="releases">
            <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
            <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

            <div class="boxHeader">
                <a class="boxRightIcon" href="${projectUrl}rss"><img class="noborder" alt="RSS" src="${cfg.staticPath}apps/mint/images/rss-inline.gif" /></a>
                <span class="bracket">[</span> Recent Releases <span class="bracket">]</span>
            </div>
            <div id="release_items" style="display: $display">
              <ul py:if="releases" class="releases">
                <?python projectName = project.getName() ?>
                <div py:for="release in releases[:5]" py:strip="True">
                    <li><a href="${projectUrl}release?id=${release.id}" title="${release.name} version ${release.version}">${truncateForDisplay(release.name, maxWords=5, maxWordLen=15)}</a>
                    <div class="version">Version ${release.version}</div></li>
                </div>
                <div py:if="not releases" py:strip="True">
                    <li>No Releases</li>
                </div>
              </ul>
              <div class="releaseNew" py:if="isOwner">
                  <a href="${projectUrl}newRelease">( Create a New Release )</a>
              </div>
              <div class="releaseMore" py:if="not isOwner and len(releases) > 5">
                  <a href="${projectUrl}releases">( More... )</a>
              </div>
            </div>
        </div>
    </div>

    <div py:def="commitsMenu(commits, display='block')" py:strip="True">
      <div py:if="commits" class="palette" id="commits">
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />

        <div class="boxHeader"><span class="bracket">[</span> Recent Commits <span class="bracket">]</span></div>
        <div id="commit_items" style="display: $display">
          <ul class="commits">
            <div py:strip="True" py:for="commit in commits">
                <li><a href="${cfg.basePath}repos/${project.getHostname()}/troveInfo?t=${commit[0]};v=${commit[2]}">${truncateForDisplay(commit[0], maxWordLen=24)}</a>
                <div class="commitTime">${commit[1]} (${timeDelta(commit[3])})</div></li>
            </div>
         </ul>
        </div>
      </div>
    </div>


    <div py:def="projectsPane()" id="projectsPane" >
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_user_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_user_right.png" alt="" />
        <div class="userBoxHeader">
            <div class="userBoxHeaderText">
              <a class="signout" href="${baseUrl}logout">( Sign Out )</a>
                <span class="userBoxBracket">[</span> ${auth.username} <span class="userBoxBracket">]</span>
            </div>
        </div>
        <div class="boxBody" py:if="not projectList">
            <a class="newuiLink" href="/ui/" target="_blank">Use the new UI</a>
            <div class="projectsPaneActionTop">
                <a href="http://${SITE}newProject">Create a new ${projectText().lower()}</a>
            </div>
            <div id="userSettings" class="projectsPaneAction">
                <a href="http://${SITE}userSettings">Edit my account</a>
            </div>
	        <div id="administer" py:if="auth.admin" class="projectsPaneAction">
                <a href="http://${SITE}admin/">Site administration</a>
            </div>
            <p class="rboJoin" >To participate in an existing ${projectText().lower()}, browse or
              search above to find the ${projectText().lower()} of interest. Open the
              ${projectText().lower()} page, select "View ${projectText().title()} Membership" and
              click "Request to join this ${projectText().lower()}".</p>
            <div class="projectsPaneBottom">
            </div>
        </div>
        <div class="boxBody" id="boxBody" py:if="projectList">
            <a class="newuiLink" href="/ui/" target="_blank">Use the new UI</a>
            <div id="switchProject" class="projectsPaneSelector">
                <?python currentProjectId = not self.project and -1 or self.project.id ?>
                <label for="switchProjectSelector">Select a ${projectText().lower()}:</label>
                <select id="switchProjectSelector" onchange="javascript:if (this.value!='--') document.location = this.value;">
                    <option value="--" py:attrs="{'selected': currentProjectId == -1 and 'selected' or None}">&nbsp;&nbsp;--</option>
                    <div py:for="level, title in [(userlevels.OWNER, '%ss I Own'%projectText().title()),
                                                  (userlevels.DEVELOPER, '%ss I Work On'%projectText().title()),
                                                  (userlevels.USER, '%ss I Use'%projectText().title())]"
                         py:strip="True">
                         <div py:strip="True" py:if="level in projectDict">
                             <optgroup label="--- ${title} ---" />
                             <option py:for="project, memberReqs in sorted(projectDict[level], key = lambda x: x[0].name.lower())" value="${project.getUrl(baseUrl)}" py:content="project.getName()" py:attrs="{'selected': (project.id == currentProjectId) and 'selected' or None}" />
                         </div>
                    </div>
                </select>
            </div>
            <div py:if="membershipReqsList" id="membershipReqs" class="projectsPaneSelector">
                <label for="membershipReqsSelector">Pending requests:</label>
                <select id="membershipReqsSelector" onchange="javascript:if (this.value!='--') document.location = this.value;">
                    <option value="--">--</option>
                    <option py:for="project in sorted(membershipReqsList, key = lambda x: x.name.lower())" value="${project.getUrl(baseUrl)}members">${project.getName()}</option>
                </select>
            </div>
            <div id="newProject" class="projectsPaneAction" py:if="auth.admin or not cfg.adminNewProjects">
                <a href="http://${SITE}newProject">Create a new ${projectText().lower()}</a>
            </div>
            <div id="userSettings" class="projectsPaneAction">
                <a href="http://${SITE}userSettings">Edit my account</a>
            </div>
            <div id="administer" py:if="auth.admin" class="projectsPaneAction">
                <a href="http://${SITE}admin/">Site administration</a>
            </div>
            <div class="projectsPaneBottom">
                &nbsp;
            </div>
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
            &nbsp;${build.getMarketingName()}</td>
        </tr>
        ${buildFiles(build)}
        <tr><td colspan="2" class="buildTypeIcon">${getBuildIcon(build)}</td></tr>
    </div>

    <div py:strip="True" py:def="getBuildIcon(build)">
        <?python icon = build.getBrandingIcon() ?>
        <a py:if="icon" title="${icon['text']}" href="${icon['href']}">
            <img class="buildTypeIcon" src="${cfg.staticPath}apps/mint/images/${icon['icon']}" alt="${icon['text']}" />
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
                <div style="font-size: smaller;" py:if="size">${size/1048576} MB<span py:if="sha1">, SHA1: ${sha1}</span></div>
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
      <div py:if="builds" class="boxPalette" id="release">
        <img class="left" src="${cfg.staticPath}apps/mint/images/block_topleft.gif" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/block_topright.gif" alt="" />
        <div class="pageBoxHeader">Download NOW</div>
        <div class="pageBoxLinks">
           <a href="${project.getUrl(baseUrl)}latestRelease">( Additional Options... )</a> <a href="http://wiki.rpath.com/wiki/rBuilder:Build_Types?version=${constants.mintVersion}" target="_blank">( Which one do I want? )</a>

            <ul class="downloadList">
                <div py:for="build in builds" py:strip="True">
                    <?python
                        buildFiles = [x for x in build.getFiles() if x['title'] not in ('diskboot.img', 'boot.iso')]
                    ?>
                    <li py:for="file in buildFiles">
                        <?python
                            title = file['title'] or ("Disc %d" % (file['idx'] + 1, ))
                            fileUrl = cfg.basePath + 'downloadImage?fileId=%d' % file['fileId']
                            extraFlags = getExtraFlags(build.troveFlavor)
                        ?>
                        <a href="$fileUrl">${build.getArch()} ${build.getMarketingName(file)}: ${title}</a>
                        <span py:omit="True" py:if="extraFlags">(${", ".join(extraFlags)})</span>
                    </li>
                </div>
            </ul>
        </div>
       <img class="left" src="${cfg.staticPath}apps/mint/images/block_bottom.gif" alt="" />
      </div>
    </div>

</html>
