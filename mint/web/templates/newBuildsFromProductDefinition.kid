<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle("Create Images From Product Definition")}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/newbuildsfromproductdefinition.js?v=${cacheFakeoutVersion}" />
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${projectsPane()}
                ${builderPane()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <h2>Create Images From Product Definition</h2>

                <p py:if="project.external">
                    Currently, building images from an external project's
                    product definition is not currently supported.
                </p>
                <p py:if="not project.external and not productVersions">
                    Your product does not have any version information set up and,
                    as such, contains no product definitions to use to create a
                    set of images. Please <a href="editVersion">create a product version</a>
                    first.
                </p>
                <form py:if="not project.external and productVersions" method="post" action="processNewBuildsFromProductDefinition" id="mainForm">
                    <div id="step1">
                        <h3>Step 1: Choose Product Version</h3>
                        <p>Choose the product version you wish to create a set of images from:</p>
                        <label for="productVersionSelector">Product Version</label>
                        <select id="productVersionSelector" name="productVersionId">
                            <option py:if="productVersions" py:content="'--'" value="-1" selected="selected" />
                            <option py:for="v in productVersions" py:content="v[2]" py:attrs="'value': v[0]" />
                        </select>
                        <span id="step1-wait" style="display: none;"><img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />&nbsp;Fetching stages for version...</span>
                    </div>

                    <div id="step2" class="hideOnReset" style="display: none;">
                        <h3>Step 2: Choose Product Stage</h3>
                        <p>Choose the stage of the product you wish to create images from:</p>
                        <label for="productStageSelector">Stage</label>
                        <select id="productStageSelector" name="productStageName">
                            <!-- inject stages -->
                        </select>
                        <span id="step2-wait" style="display: none;"><img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />&nbsp;Fetching tasks for stage...</span>
                    </div>

                    <div id="step3-confirm" class="hideOnReset" style="display: none;">
                        <h3>Step 3: Confirm the Set of Images</h3>
                        <p id="taskListHeader">The following images will be built:</p>
                        <dl id="taskList" />
                        <p>Note: The actual number of images generated may be
                            different from the above list in the following cases:</p>
                           <ul>
                               <li>The image group for a build was not cooked with a flavor that satisfies an image's flavor or architectural requirements</li>
                               <li>The image group for a build was cooked with several different flavors that each satisfy an image's flavor or architectural requirements</li>
                           </ul>
                    </div>

                    <div id="step2-error" class="hideOnReset" style="display: none;">

                        <h3>Error</h3>
                        <p>Failed to find the product definition for the specified
                           version. Please select a different version and try again.
                        </p>
                    </div>
                    <div id="step3-error" class="hideOnReset" style="display: none;">
                        <h3>Error</h3>
                        <p>This product version is not configured to build any
                           images for the selected stage. Choose a different
                           stage and/or product version to continue.
                        </p>
                    </div>
                    <div id="action-buttons" class="hideOnReset" style="display: none;">
                        <input id="submit-button" type="submit" name="action" disabled="disabled" value="Submit" />
                        <input type="submit" name="action" value="Cancel" />
                    </div>
                </form>
            </div>
        </div>
    </body>
</html>
