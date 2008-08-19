/*
 Copyright (c) 2008 rPath, Inc.
 All rights reserved
*/

function parseXHRresponseIE(xhr) {
    xmlDoc=new ActiveXObject("Microsoft.XMLDOM");
    xmlDoc.async=false;
    xmlDoc.validateOnParse = false;
    if (!xmlDoc.loadXML(xhr.responseText))
    {
      //TODO: Need to log an error
    }
    return xmlDoc;
}

function parseResponseAndAppendTo(xhr, wanted_element, append_to) {
    var xmlDoc = null;
    try { //Internet Explorer
        loaded = jQuery(xhr.responseText);
        //In IE, it appears to load it discarding the body tags, so no selection is needed
        loaded.appendTo(append_to);
    }
    catch(e) {
      try { //Firefox, Mozilla, Opera, etc.
        parser=new DOMParser();
        xmlDoc=parser.parseFromString(xhr.responseText, "text/xml");
        jQuery('#' + wanted_element, xmlDoc).appendTo(append_to);
      }
      catch(e) {throw e;}
    }
}

function finished_load_packageList(xhr, textStatus)
{
    //We don't use the "success" callback because the data is too big to put on the stack
    // See http://dev.jquery.com/ticket/3250
    if (textStatus == 'success') {
        xmlDoc = parseResponseAndAppendTo(xhr, 'packageList', '#packageList_troveList');
        // Set up the links to the anchors
        add_anchor_links();
        // Set the odd/even classes
        //var rows = jQuery('tr[id=packageList_trove_row]');
        //odd_and_even(rows);
        add_filter_handler();
        jQuery('#loading_wait').hide();
        jQuery('#packageList_troveList').show();
        jQuery('#selectPackagesFormSubmit').get(0).disabled=false;
        jQuery('input[name=jumpto]').get(0).disabled=false;
    }
}

var lastselected = null;

function jump_to_item()
{
    linkname = jQuery(this).text();
    divOffset = jQuery('#packageList_troveList').offset().top;
    row = jQuery('tr[name=row_' + linkname + ']');
    pOffset = row.offset().top;
    var pScroll = pOffset - divOffset - 2;
    jQuery('#packageList_troveList').animate({scrollTop: '+=' + pScroll + 'px'}, 50, 'swing');
    obj = jQuery('input#checkbox_' + linkname).attr('checked', 'checked');
    if (lastselected)
        lastselected.removeClass('selected');
    lastselected = row.addClass('selected');
    return false;
}

function reset_filter()
{
    jQuery('#filter_selections').empty().hide('fast');
}

var troveNames = [];

function get_trove_list()
{
    troveNames = jQuery('.packageList_trove_name').map(function(index, domElem) {
        return jQuery(domElem).text().replace(/^\s+|\s+$/g,"");
    });
}

function pkg_filter(val){
    if (troveNames.length == 0)
        get_trove_list();
    if (!val) {
        reset_filter();
        return true;
    }
    regex = new RegExp(val, 'i');
    var results = jQuery('#filter_selections');
    wrapper = jQuery('#filter_navigation_link_template').clone();
    wrapper.attr('id', 'filter_navigation_link');
    wrapper.show();
    results.empty();
    var added = 0;
    for (var i = 0; i < troveNames.length; i++) {
        if (troveNames[i].search(regex) != -1){
            wclone = wrapper.clone()
            wclone.append(document.createTextNode(troveNames[i]));
            added += 1;
            //results.append(document.createTextNode('\n'));
            results.append(wclone);
        }
    }
    if (added <= 0) {
        results.append('<div id="no_package">No packages match the filter term.</div>');
    }
    jQuery('div[id=filter_navigation_link]').click(jump_to_item);
    results.show('fast');
    return true;
}

function pkgs_live_filter(e)
{
    searchval = jQuery(this).val();
    switch(e.which) {
        case 13:
        case 10:
        case 9:
            //ignore enter and tab They'll be picked up by onchange
            return true;
    };

    if (searchval.length < 2)
        reset_filter();
    else
        pkg_filter(searchval);
}

function add_filter_handler() {
    var search_box = jQuery('input[name=jumpto]');
    //search_box.change( function (e) { pkg_filter(this.value) });
    search_box.keyup( pkgs_live_filter );
    //Enable the clear button
    jQuery('#jumpto_box_clear').click(function() {
        jQuery('input[name=jumpto]').val('');
        reset_filter();
        return false;
    });
}

function animate_scroll_to(eventObj) {
    var divOffset = jQuery('#packageList_troveList').offset().top;
    var pOffset = jQuery('#' + this.id + "_target").offset().top;
    var pScroll = pOffset - divOffset;
    jQuery('#packageList_troveList').animate({scrollTop: '+=' + pScroll + 'px'}, 300, 'swing');
    return false;
}

function linkhere(index, domElement)
{
    var linktmp = jQuery('#packageList_navigation_link_template > a').clone().get(0);
    linktmp.id = 'packageList_navigation_link';
    linktmp.href = '#' + domElement.id;
    var id = domElement.id.replace('_target', '');
    var res = jQuery('#' + id).wrapInner(linktmp)

    res.click(animate_scroll_to);
}

function add_anchor_links()
{
    jQuery('h3.packageList_section_header').map(linkhere);
}

jQuery(document).ready(function () {
    //Show the spinner, and start loading the trove list
    jQuery('#loading_wait').show();
    jQuery.ajax({
        type: 'GET',
        url: 'packageList',
        complete: finished_load_packageList,
        dataType: 'html',
        cache: false,
        error:
            function(req, textStatus, errorThrown) {
                alert("Could not load the package list");
            }
        });
    });
