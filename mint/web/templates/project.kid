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
            <li><a href="$projectUrl/releases"><strong py:strip="lastchunk not in ('release', 'releases')">Releases</strong></a></li>

            <li><a href="${cfg.basePath}repos/${project.getHostname()}/browse"><strong py:strip="lastchunk not in ('browse', 'troveInfo')">Repository</strong></a></li>
            <li><a href="$projectUrl/members"><strong py:strip="lastchunk != 'members'">Project Members</strong></a></li>
            <li><a href="$projectUrl/mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <td py:def="projectsPane()" id="right" class="projects">
        <div class="pad">
            <h3>My Projects</h3>
            <p py:if="not auth.authorized">
                <p>You must be logged in for your projects to be displayed.</p>
                <p>To login, use the form above, or <a href="${cfg.basePath}register">create a new account</a></p>
            </p>
            <ul py:if="auth.authorized">
                <li py:if="projectList" 
                    py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="${cfg.basePath}project/${project.getHostname()}/">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                        <p py:if="not level and project.listJoinRequests()">
                            <a href="${cfg.basePath}project/${project.getHostname()}/members"><b style="color: red;">Requests Pending</b></a>
                        </p>
                </li>
                <li py:if="not projectList">
                    <p>You are not a member of any projects.</p>
                    <p><a href="${cfg.basePath}projects">Browse the list of projects to find one to join</a></p>
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
