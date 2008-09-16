/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/

var resetNewBuildsPage = function () {
    jQuery('.hideOnReset').hide();
    jQuery('#submit-button').attr('disabled', 'disabled');
};

var onProductStageSelection = function () {
    // Retrieve the current list builds that will be created
    // if the build set is submitted.
    //
    // Call the backend with the versionId and stage to
    // get a list of dictionaries with the following structure:
    // - buildName:  the name of the build definition
    // - buildTypeName: the type of the build (e.g. 'Installable ISO')
    // - imageGroup: the name of the top-level group the build is
    //               built from
    // - buildFlavorName: a string representing the flavor of the build
    //               should be human-readable or 'custom' with the
    //               flavor specification

    var _callback = function (aReq) {
        var buildTaskList = evalJSONRequest(aReq);
        var taskListNode = jQuery('#taskList');

        jQuery('#step1-wait').hide();

        taskListNode.empty();

        jQuery('#action-buttons').show();

        if (buildTaskList.length == 0) {
            jQuery("#step2-error").show();
        } else {
            jQuery.each(buildTaskList, function () {
                taskListNode.append('<dt>'+this['buildName']+'</dt><dd>'+this['buildFlavorName']+' '+this['buildTypeName']+'<br /><span class="imagegroup">Image Group: '+this['imageGroup']+'</span></dd>');
            jQuery("#step2-confirm").show();
            jQuery('#submit-button').removeAttr('disabled');
            });
        }
    };

    jQuery('#step2-error,#step2-confirm,#action-buttons').hide();

    var productVersionSelector = jQuery('#productVersionSelector').get(0);
    var productStageSelector = jQuery('#productStageSelector').get(0);

    if (productStageSelector.selectedIndex == 0) {
        return;
    }

    var productVersionId = parseInt(productVersionSelector.value);
    var stageName = productStageSelector.value;

    jQuery('#step1-wait').show();

    // Make the request
    var req = new JsonRpcRequest("jsonrpc/",
            "getBuildTaskListForDisplay");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(_callback);
    req.send(true, [productVersionId, stageName]);

};

var onProductVersionSelection = function () {

    var _callback = function (aReq) {
        var stageList = evalJSONRequest(aReq);
        jQuery('#step0').hide();
        jQuery(productStageSelector).empty();
        jQuery(productStageSelector).append('<option>--</option>');

        // XXX this needs better error handling on the server side
        // XXX for now, we'll use this hack... ugh --sgp
        if (stageList.length == 0 || stageList[0] == 'ProductDefinitionVersionNotFound') {
            jQuery("#step1-error").show();
            return;
        }
        jQuery.each(stageList, function () {
            jQuery(productStageSelector).append('<option value="'+this+'">'+this+'</option>');
        });
        jQuery("#step1").show();
    };

    var productVersionSelector = jQuery('#productVersionSelector').get(0);
    var productStageSelector = jQuery('#productStageSelector').get(0);

    if (!productVersionSelector.value) {
        return;
    }

    var productVersionId = parseInt(productVersionSelector.value);

    jQuery('#step0-wait').show();
    var req = new JsonRpcRequest("jsonrpc/",
            "getStagesForProductVersion");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(_callback);
    req.send(true, [productVersionId]);
};

jQuery(document).ready(function () {
    jQuery('#productStageSelector').change(onProductStageSelection);
});

