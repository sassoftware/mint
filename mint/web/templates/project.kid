<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
    <div py:def="projectResourcesMenu" id="browse" class="palette">
        <?python
            lastchunk = req.uri[req.uri.rfind('/')+1:]
        ?>
        <h3>Project Resources</h3>
        <ul>
            <li><a href="/"><strong py:omit="req.uri != '/'">Project Home</strong></a></li>
            <li><a href="/releases"><strong py:omit="lastchunk != 'releases'">Releases</strong></a></li>

            <li><a href="/conary/browse"><strong py:omit="req.uri != '/conary/browse'">Repository</strong></a></li>
            <li><a href="/members"><strong py:omit="lastchunk != 'members'">Project Members</strong></a></li>
            <li><a href="/mailingLists"><strong py:omit="lastchunk != 'mailingLists'">Mailing Lists</strong></a></li>
            <li><a href="#"><strong py:omit="lastchunk != 'bugs'">Bug Tracking</strong></a></li>
        </ul>
    </div>

    <td py:def="projectsPane()" id="right" class="projects">
        <div class="pad">
            <h3>My Projects</h3>
            <p py:if="not auth.authorized">
                You must be logged in for your projects to be displayed.
            </p>
            <ul py:if="auth.authorized">
                <li py:for="project, level in sorted(projectList, key = lambda x: x[0].getName())">
                    <a href="http://${project.getHostname()}/">
                        ${project.getName()}</a><br/>
                        ${userlevels.names[level]}
                </li>
            </ul>
            <ul py:if="auth.authorized">
                <li>
                    <a href="newProject">Create a new project</a>
                </li>
            </ul>
        </div>
    </td>
</html>
