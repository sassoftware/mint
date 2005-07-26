<?xml version='1.0' encoding='UTF-8'?>
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
</html>
