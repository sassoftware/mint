<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels

?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
    <div py:def="projectResourcesMenu" id="browse" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
            projectUrl = "%sproject/%s" % (cfg.basePath, project.getHostname())
        ?>
        <h3>Project Resources</h3>
        <ul>
            <li><a href="$projectUrl/"><strong py:strip="lastchunk != ''">Project Home</strong></a></li>
            <li><a href="$projectUrl/releases"><strong py:strip="lastchunk not in ('release', 'releases', 'newRelease', 'editRelease')">Releases</strong></a></li>

            <li><a href="${cfg.basePath}repos/${project.getHostname()}/browse"><strong py:strip="lastchunk not in ('browse', 'troveInfo')">Repository</strong></a></li>
            <li py:if="not project.external"><a href="$projectUrl/members"><strong py:strip="lastchunk != 'members'">Project Members</strong></a></li>
            <li py:if="not project.external"><a href="$projectUrl/mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <td py:def="projectsPane()" id="right" class="projects">
        <div py:if="not auth.authorized" class="pad">
            <h3>Start Using rBuilder Online Today</h3>

            <p>If you are new to rBuilder Online, create
            your new account by using the
            <a href="${cfg.basePath}register"><strong>new account</strong></a>
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
                <a href="${cfg.basePath}newProject"><strong>here</strong></a>.</p>

            <p>To join an existing project, use the browse or search boxes
            in the left sidebar to find a project that interests you.
            Then, click on the project name, and click on the "Request to join"
            link to submit your request to the project's owners.</p>
        </div>
        <div py:if="auth.authorized and projectList" class="pad">
            <h3>My Projects</h3>
            <ul>
                <li py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="${cfg.basePath}project/${project.getHostname()}/">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                        <span py:if="not level and project.listJoinRequests()">
                            <a href="${cfg.basePath}project/${project.getHostname()}/members"><b style="color: red;">Requests Pending</b></a>
                        </span>
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="${cfg.basePath}newProject"><strong>Create a new project</strong></a>
                </li>
            </ul>
        </div>
    </td>
</html>
