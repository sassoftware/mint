/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/
var currentBdefSerial = 0;
var currentUsourceSerial = 0;

jQuery(document).ready(function () {

    currentBdefSerial = jQuery(".pd-builddef-deleter").length;
    currentUsourceSerial = jQuery(".pd-usource-deleter").length;

    jQuery('select.pd-builddef-picker-buildType').change(function() {
        var builddefElement = jQuery(this).parents('tr').get(0);
        var builddefmoreElement= jQuery(builddefElement).next().get(0);
        var buildtype = this.value;
        var buildtypeclass = '.it-'+buildtype;

        jQuery(builddefmoreElement).find('div.it-'+buildtype).each(function () {
            jQuery(this).show();
            jQuery(this).find(':input').removeAttr('disabled');
        });
        jQuery(builddefmoreElement).find('div:not(.it-'+buildtype+')').each(function () {
            if (jQuery(this).is(':not(.clearleft)')) {
                jQuery(this).hide();
            }
            jQuery(this).find(':input').attr('disabled', 'disabled');
        });
    });

    jQuery('.pd-builddef-adder,.pd-builddef-expander,.pd-builddef-deleter,.pd-usource-adder,.pd-usource-deleter').hover(function () {
            var imgbutton = jQuery(this).find('img').get(0);
            imgbutton.src = imgbutton.src.replace('.gif', '_h.gif');
        }, function() {
            var imgbutton = jQuery(this).find('img').get(0);
            imgbutton.src = imgbutton.src.replace('_h.gif', '.gif');
    });

    jQuery('.pd-builddef-expander').click(function () {
            var imgbutton = jQuery(this).find('img').get(0);
            var builddefId = "#" + jQuery(this).parents().get(1).id;
            var builddefmoreId = builddefId + "-more";
            if (jQuery(builddefId).attr('class') == 'pd-builddef-expanded') {
                jQuery(builddefmoreId).hide();
                jQuery(builddefId).removeAttr('class');
                jQuery(builddefmoreId).removeAttr('class');
            } else {
                jQuery(builddefmoreId).show();
                jQuery(builddefId).attr('class', 'pd-builddef-expanded');
                jQuery(builddefmoreId).attr('class', 'pd-builddef-more');
            }
    });

    jQuery('.pd-builddef-deleter').click(function () {
            var builddefId = "#" + jQuery(this).parents().get(1).id;
            var builddefmoreId = builddefId + '-more';
            jQuery(builddefId).remove();
            jQuery(builddefmoreId).remove();
            
            // show the no entries found if last one removed
            var templateDomBits = jQuery('#pd-builddefs > tbody').clone(true);
            var numEntries = 0;
            templateDomBits.find('tr').each(function () {
                numEntries += 1;
            });
            if(numEntries <= 1) {
                jQuery('#pd-builddef-empty').show();
            }
    });

    jQuery('.pd-builddef-adder').click(function () {
        currentBdefSerial++;
        var templateDomBits = jQuery('#pd-builddef-bt-all > tbody').clone(true);
        templateDomBits.find(':disabled').removeAttr('disabled');
        templateDomBits.find('label').each(function () {
            this.htmlFor = this.htmlFor.replace('bt', String(currentBdefSerial));
        });
        templateDomBits.find('input,select').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
            if (this.name) { this.name = this.name.replace('bt', String(currentBdefSerial)); }
        });
        templateDomBits.find('tr').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
        });
        templateDomBits.find('select').change();
        templateDomBits.children().appendTo('#pd-builddefs > tbody');
        
        // hide the no entries found message
        jQuery('#pd-builddef-empty').hide();
    });

    jQuery('.pd-usource-deleter').click(function () {
            var usourceId = "#" + jQuery(this).parents().get(1).id;
            jQuery(usourceId).remove();
            // show the no entries found if last one removed
            var templateDomBits = jQuery('#pd-usource > tbody').clone(true);
            var numEntries = 0;
            templateDomBits.find('tr').each(function () {
                numEntries += 1;
            });
            if(numEntries <= 1) {
                jQuery('#pd-usource-empty').show();
            }
    });
    
    jQuery('.pd-usource-adder').click(function () {
        currentUsourceSerial++;
        var templateDomBits = jQuery('#pd-usource-bt-all > tbody').clone(true);
        templateDomBits.find(':disabled').removeAttr('disabled');
        templateDomBits.find('label').each(function () {
            this.htmlFor = this.htmlFor.replace('bt', String(currentUsourceSerial));
        });
        templateDomBits.find('input,select').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentUsourceSerial)); }
            if (this.name) { this.name = this.name.replace('bt', String(currentUsourceSerial)); }
        });
        templateDomBits.find('tr').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentUsourceSerial)); }
        });
        templateDomBits.find('select').change();
        templateDomBits.children().appendTo('#pd-usource > tbody');
        
        // hide the no entries found message
        jQuery('#pd-usource-empty').hide();
    });
});

// given a project path (i.e. /project/foo) and version id, redirect to the 
// proper edit version page
function editVersionRedirect(projectPath, versionId) {
                
    if(versionId >= 0) {
    
       // makes sure projectPath ends in slash
       if(projectPath.charAt(projectPath.length -1) != '/') {
           projectPath += '/';
       }
    
       location = projectPath + 'editVersion?id=' + versionId;
    }
}