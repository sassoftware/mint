<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels
    from mint.mint import upstream

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
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" />
        <div class="boxHeader">Project Resources</div>
        <ul>
            <li><a href="$projectUrl"><strong py:strip="lastchunk != ''">Project Home</strong></a></li>
            <li><a href="${projectUrl}releases"><strong py:strip="lastchunk not in ('release', 'releases', 'newRelease', 'editRelease')">Releases</strong></a></li>
            <li><a href="${projectUrl}../../repos/${project.getHostname()}/browse"><strong py:strip="lastchunk not in ('browse', 'troveInfo')">Repository</strong></a></li>
            <li py:if="isDeveloper"><a href="${projectUrl}groups"><strong py:strip="lastchunk not in ('groups', 'editGroup', 'editGroup2', 'newGroup', 'pickArch', 'cookGroup')">Group Builder</strong></a></li>
            <li py:if="not project.external"><a href="${projectUrl}members"><strong py:strip="lastchunk != 'members'">Members</strong></a></li>
            <li py:if="not project.external and cfg.EnableMailLists"><a href="${projectUrl}mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <div py:def="releasesMenu(releaseList, isOwner=False, display='block')" py:strip="True">
        <?python
            projectUrl = project.getUrl()
        ?>
        <div py:if="isOwner or releaseList" class="palette" id="releases">
            <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" />
            <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" />

            <div class="boxHeader">Recent Releases</div>
            <div id="release_items" style="display: $display">
                <ul>
                <?python
                    upstreamList = [upstream(x.getTroveVersion()) for x in releaseList[:5]]
                    # create a dictionary with counts of duplicate upstream versions
                    counts = dict(zip(set(upstreamList), [upstreamList.count(x) for x in set(upstreamList)]))
                ?>
                <li class="release"
                    py:if="releaseList" py:for="release in sorted(releaseList[:5], key=lambda x: x.getTroveVersion(), reverse=True)">
                    <a href="${projectUrl}release?id=${release.getId()}">
                        Version ${condUpstream(counts, release.getTroveVersion())} for ${release.getArch()}
                    </a>
                </li>
                <li class="release" py:if="not releaseList">
                    No Releases
                </li>
                <div class="release" py:if="isOwner" style="text-align: right; padding-right:8px;">
                    <a href="${basePath}newRelease"><strong>Create a new release</strong></a>
                </div>
                <div class="release" py:if="not isOwner and len(releaseList) > 5" style="text-align: right; padding-right:8px;">
                    <a href="${basePath}releases"><strong>More...</strong></a>
                </div>
              </ul>
            </div>
      </div>
    </div>

    <div py:def="commitsMenu(commits, display='block')" py:strip="True">
      <div py:if="commits" class="palette" id="commits">
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" />


        <div class="boxHeader">Recent Commits</div>
        <div id="commit_items" style="display: $display">
          <ul>
            <li class="release" py:for="commit in commits">
                <a
                    href="${cfg.basePath}repos/${project.getHostname()}/troveInfo?t=${commit[0]};v=${commit[2]}">${commit[0]}=${commit[1]}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div py:def="projectsPane()" id="projectsPane" >
        <div py:if="not auth.authorized" strip="True">
            Silly web programmer. projects pane is for logged in users.
        </div>
        <div py:if="not projectList" strip="True">
            <h3>Get Involved</h3>

            <p>Now's the time to get involved with the ${cfg.productName}
            community. There are several ways you can do this:</p>

            <ul>
                <p>You can <a
                href="http://${SITE}newProject"><strong>create a new
                project</strong></a>.</p>

                <p>You can join an existing project.</p>
            </ul>

            <p>To join an existing project, use the browse or search boxes
            in the left sidebar to find a project that interests you.
            Then, click on the project name, and click on the "Request to join"
            link to submit your request to the project's owners.</p>
        </div>
        <div py:if="projectList" strip="True">
            <img class="left" src="${cfg.staticPath}apps/mint/images/header_orange_left.png" />
            <img class="right" src="${cfg.staticPath}apps/mint/images/header_orange_right.png" />
            <div class="boxHeader">Welcome ${auth.username}</div>
            <ul>
                <li py:for="project, level in sorted(projectList, cmp = userlevels.myProjectCompare)">
                    <a href="${project.getUrl()}">
                        ${project.getNameForDisplay()}</a><br/>
                        ${userlevels.names[level]}
                        <span py:if="not level and project.listJoinRequests()">
                            <a href="${project.getUrl()}members"><b style="color: red;">Requests Pending</b></a>
                        </span>
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="http://${SITE}newProject"><strong>Create a new project</strong></a>
                </li>
            </ul>
        </div>
        <p><a href="http://${cfg.siteHost}${cfg.basePath}logout">Sign Out</a></p>
    </div>
</html>
