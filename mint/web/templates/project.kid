<?xml version='1.0' encoding='UTF-8'?>
<?python #need a comment?
    from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
    <div py:def="projectResourcesMenu" id="browse" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
            projectUrl = "http://%s/project/%s" % (siteHost, project.getHostname())
        ?>
        <h3>Project Resources</h3>
        <ul>
            <li><a href="$projectUrl"><strong py:strip="req.uri != '/'">Project Home</strong></a></li>
            <li><a href="$projectUrl/releases"><strong py:strip="lastchunk not in ('release', 'releases')">Releases</strong></a></li>

            <li><a href="http://${cfg.reposHost}.${cfg.domainName}/${project.getHostname()}/browse"><strong py:strip="req.uri != '/conary/browse'">Repository</strong></a></li>
            <li><a href="$projectUrl/members"><strong py:strip="lastchunk != 'members'">Project Members</strong></a></li>
            <li><a href="$projectUrl/mailingLists"><strong py:strip="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li py:if="0"><a href="#"><strong py:strip="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <td py:def="projectsPane()" id="right" class="projects">
        <div class="pad">
            <h3>My Projects</h3>
            <p py:if="not auth.authorized">
                You must be logged in for your projects to be displayed.
            </p>
            <ul py:if="auth.authorized">
                <li py:if="projectList" 
                    py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="http://$siteHost/project/${project.getHostname()}/">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                </li>
                <li py:if="not projectList">
                    You are not a member of any projects.
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="http://$siteHost/newProject"><strong>Create a new project</strong></a>
                </li>
            </ul>
        </div>
    </td>
</html>
