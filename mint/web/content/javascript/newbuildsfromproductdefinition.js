/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/

var resetNewBuildsPage = function () {
    jQuery('.hideOnReset').hide();
    jQuery('#productStageSelector');
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
        taskListNode.empty();

        if (buildTaskList.length == 0) {
            jQuery("#step3-error").show();
        } else {
            jQuery.each(buildTaskList, function () {
                taskListNode.append("<dt>"+this['buildName']+"</dt><dd>"+this['buildTypeName']+", "+this['imageGroup']+", "+this['buildFlavorName']+"</dd>")
            jQuery("#step3-confirm").show();
            });
        }
    };

    var productVersionId = parseInt(jQuery('#productVersionSelector').get(0).value);
    var stageName = jQuery('#productStageSelector').get(0).value;

    // Don't do anything if nothing useful is selected
    if (!stageName) {
        return;
    }

    // Make the request
    var req = new JsonRpcRequest("jsonrpc/",
            "getBuildTaskListForDisplay");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(_callback);
    req.send(false, [productVersionId, stageName]);

};

var onProductVersionSelection = function () {

    var _callback = function (aReq) {
        var stageList = evalJSONRequest(aReq);
        var productStageSelector = jQuery("#productStageSelector");
        productStageSelector.empty();
        productStageSelector.append('<option>--</option>');
        jQuery.each(stageList, function () {
            productStageSelector.append('<option value="'+this+'">'+this+'</option>');
        });
        jQuery("#step2").show();
    };

    resetNewBuildsPage(); // just to be sure

    var productVersionId = parseInt(jQuery('#productVersionSelector').get(0).value);
    if (productVersionId == -1) {
        return;
    }

    var req = new JsonRpcRequest("jsonrpc/",
            "getStagesForProductVersion");
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(_callback);
    req.send(false, [productVersionId]);

};

jQuery(document).ready(function () {
    jQuery('#productVersionSelector').change(onProductVersionSelection);
    jQuery('#productStageSelector').change(onProductStageSelection);
});

