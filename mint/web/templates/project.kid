<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels, releasetypes
    from mint.mint import upstream
    from mint.helperfuncs import truncateForDisplay
    from mint.mint import timeDelta

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
            isOwner = userLevel == userlevels.OWNER or auth.admin
            isDeveloper = userLevel in userlevels.WRITERS or auth.admin
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader">Project Resources</div>
        <ul>
            <li><a href="$projectUrl"><strong py:strip="lastchunk != ''">Project Home</strong></a></li>
            <li><a href="${projectUrl}releases"><strong py:strip="lastchunk not in ('release', 'releases', 'newRelease', 'editRelease')">Releases</strong></a></li>
            <li><a href="${projectUrl}../../repos/${project.getHostname()}/browse"><strong py:strip="lastchunk not in ('browse', 'troveInfo')">Repository</strong></a></li>
            <li py:if="isDeveloper"><a href="${projectUrl}groups"><strong py:strip="lastchunk not in ('groups', 'editGroup', 'editGroup2', 'newGroup', 'pickArch', 'cookGroup')">Group Builder</strong></a></li>
            <li><a href="${projectUrl}members"><strong py:strip="lastchunk != 'members'">Members</strong></a></li>
            <li><a href="${projectUrl}mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
            <li><a href="${projectUrl}help"><strong py:strip="lastchunk != 'help'">Help</strong></a></li>
        </ul>
    </div>

    <div py:def="releasesMenu(releaseList, isOwner=False, display='block')" py:strip="True">
        <?python
            projectUrl = project.getUrl()
        ?>
        <div py:if="isOwner or releaseList" class="palette" id="releases">
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
              <?python
                  upstreamList = [upstream(x.getTroveVersion()) for x in releaseList[:5]]
                  # create a dictionary with counts of duplicate upstream versions
                  counts = dict(zip(set(upstreamList), [upstreamList.count(x) for x in set(upstreamList)]))
              ?>
              <dl py:if="releaseList">
                <?python projectName = project.getName() ?>
                <div py:strip="True" py:for="release in sorted(releaseList[:5], key=lambda x: x.getTroveVersion(), reverse=True)">
                  <?python
                      # XXX: this code should not be here after the new
                      #      release metaphor is put in place.
                      if projectName != release.getName():
                          releaseName = truncateForDisplay(release.getName(), maxWords=5, maxWordLen=8)
                      else:
                          releaseName = "Version " + condUpstream(counts, release.getTroveVersion())
                          desc = "%s %s (%s)" % (release.getArch(), releasetypes.typeNamesShort[release.imageTypes[0]], timeDelta(release.timePublished))
                  ?>
                    <dt><a href="${projectUrl}release?id=${release.getId()}">${releaseName}</a></dt>
                    <dd>${desc}</dd>
                </div>
              </dl>
              <div py:if="not releaseList">
                 <dl><dt>No Releases</dt></dl>
              </div>
              <div class="release" py:if="isOwner" style="text-align: right; padding-right:8px;">
                  <a href="${projectUrl}newRelease"><strong>Create a new release</strong></a>
              </div>
              <div class="release" py:if="not isOwner and len(releaseList) > 5" style="text-align: right; padding-right:8px;">
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
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_orange_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_orange_right.png" alt="" />
        <div class="boxHeader">
            <div class="boxHeaderText">
                <span>${auth.username}</span>
                <a style="float: right; font-size: 75%;" href="http://${cfg.siteHost}${cfg.basePath}logout">
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
            in the left sidebar to find a project that interests you.
            Then, click on the project name, and click on the "Request to join"
            link to submit your request to the project's owners.</p>
            <div id="userSettings"><a href="http://${SITE}userSettings"><strong>Edit my account</strong></a></div>
	    <div id="administer" py:if="auth.admin"><a href="http://${SITE}administer"><strong>Administrator settings</strong></a></div>
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
            <div id="newProject"><a href="http://${SITE}newProject"><strong>Create a new project</strong></a></div>
            <div id="userSettings"><a href="http://${SITE}userSettings"><strong>Edit my account</strong></a></div>
            <div id="administer" py:if="auth.admin"><a href="http://${SITE}administer"><strong>Administrator settings</strong></a></div>
        </div>
    </div>
</html>
