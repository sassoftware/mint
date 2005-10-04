<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels
    from mint.mint import upstream
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

    <div py:def="projectResourcesMenu" id="project" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
            projectUrl = project.getUrl()
            isOwner = userLevel == userlevels.OWNER or auth.admin
        ?>
        <h3>Project Resources</h3>
        <ul>
            <li><a href="$projectUrl"><strong py:strip="lastchunk != ''">Project Home</strong></a></li>
            <li><a href="${projectUrl}releases"><strong py:strip="lastchunk not in ('release', 'releases', 'newRelease', 'editRelease')">Releases</strong></a></li>

            <li><a href="${cfg.basePath}/repos/${project.getHostname()}/browse"><strong py:strip="lastchunk not in ('browse', 'troveInfo')">Repository</strong></a></li>
            <li py:if="not project.external"><a href="${projectUrl}members"><strong py:strip="lastchunk != 'members'">Members</strong></a>
                <li py:if="isOwner"><a href="${cfg.basePath}/repos/${project.getHostname()}/pgpAdminForm">Manage Signing Keys</a></li>
            </li>
            <li py:if="not project.external"><a href="${projectUrl}mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <div py:def="releasesMenu(releases, isOwner=False, display='block')" py:strip="True">
      <div py:if="isOwner or releases" class="palette" id="releases">
        <h3 onclick="javascript:toggle_display('release_items');">
            <img id="release_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" border="0" />
            Recent Releases
        </h3>
        <div id="release_items" style="display: $display">
          <ul>
            <li class="release" py:if="releases" py:for="release in releases[:3]">
                <a href="${basePath}release?id=${release.getId()}">
                    Version ${upstream(release.getTroveVersion())} for ${release.getArch()}
                </a>
            </li>
            <li class="release" py:if="not releases">
                No Releases
            </li>
            <div class="release" py:if="isOwner" align="right" style="padding-right:8px;">
                <a href="newRelease"><strong>Create a new release...</strong></a>
            </div>
            <div class="release" py:if="not isOwner and len(releases) > 3" align="right" style="padding-right:8px;">
                <a href="releases"><strong>More...</strong></a>
            </div>
          </ul>
        </div>
      </div>
    </div>

    <div py:def="commitsMenu(commits, display='block')" py:strip="True">
      <div py:if="commits" class="palette" id="commits">
        <h3 onclick="javascript:toggle_display('commit_items');">
            <img id="commit_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" border="0" />
            Recent Commits
        </h3>
        <div id="commit_items" style="display: $display">
          <ul>
            <li class="release" py:for="commit in commits">
                <a href="/repos/${project.getHostname()}/troveInfo?t=${commit[0]}">
                    ${commit[0]}=${commit[1]}
                </a>
            </li>
          </ul>
        </div>
      </div>
    </div>


    <td py:def="projectsPane()" id="right" class="projects">
        <div py:if="not auth.authorized" class="pad">
            <h3>Start Using rBuilder Online Today</h3>

            <p>If you are new to rBuilder Online, create
            your new account by using the
            <a href="http://$SITE/register"><strong>new account</strong></a>
            link above.</p>

            <p>If you already have an account, use the above form to login.</p>
        </div>
        <div py:if="auth.authorized and not projectList" class="pad">
            <h3>Get Involved</h3>

            <p>Now's the time to get involved with the rBuilder Online
            community. There are two ways you can do this:</p>

            <ul>
                <p>You can create a new project.</p>

                <p>You can join an existing project.</p>
            </ul>

            <p>To create a new project, click
                <a href="http://$SITE/newProject"><strong>here</strong></a>.</p>

            <p>To join an existing project, use the browse or search boxes
            in the left sidebar to find a project that interests you.
            Then, click on the project name, and click on the "Request to join"
            link to submit your request to the project's owners.</p>
        </div>
        <div py:if="auth.authorized and projectList" class="pad">
            <h3>My Projects</h3>
            <ul>
                <li py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="${project.getUrl()}">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                        <span py:if="not level and project.listJoinRequests()">
                            <a href="${project.getUrl()}/members"><b style="color: red;">Requests Pending</b></a>
                        </span>
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="http://$SITE/newProject"><strong>Create a new project</strong></a>
                </li>
            </ul>
        </div>
    </td>
</html>
