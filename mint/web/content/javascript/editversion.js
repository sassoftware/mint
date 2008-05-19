/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/
var currentBdefSerial = 0;
var currentUsourceSerial = 0;

jQuery(document).ready(function () {

    currentBdefSerial = jQuery(".pd-builddef-deleter").length;
    currentUsourceSerial = jQuery(".pd-usources-deleter").length;

    jQuery('select.pd-builddef-picker-buildType').change(function() {
        var builddefElement = jQuery(this).parents('tr').get(0);
        var builddefmoreElement= jQuery(builddefElement).next().get(0);
        var archSelectorElement = jQuery(builddefElement).children('td').get(2);
        var buildtype = this.value;
        var buildtypeclass = '.it-'+buildtype;
        var archtypeclass = '.arch-'+buildtype;

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
        
        // handle arch selectors
        jQuery(archSelectorElement).find('select:not(.arch-'+buildtype+')').each(function () {
            if (jQuery(this).is(':not(.clearleft)')) {
                jQuery(this).hide();
                jQuery(this).attr('disabled', 'disabled');
            }
        });
        jQuery(archSelectorElement).find('select.arch-'+buildtype).each(function () {
            jQuery(this).show();
            jQuery(this).removeAttr('disabled');
        });
    });

    jQuery('.pd-builddef-adder,.pd-builddef-expander,.pd-builddef-deleter,.pd-usources-adder,.pd-usources-deleter').hover(function () {
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
        var templateDomBits = jQuery('#pd-builddef-bt-all > tbody').clone(true);
        templateDomBits.find(':disabled').removeAttr('disabled');
        templateDomBits.find('label').each(function () {
            this.htmlFor = this.htmlFor.replace('bt', String(currentBdefSerial));
        });
        templateDomBits.find('input,select').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
            if (this.name) { this.name = this.name.replace('bt', String(currentBdefSerial)); }
            if (this.value == 'NEWBUILD') { this.value = "New Build " + currentBdefSerial; }
        });
        templateDomBits.find('tr').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
        });
        templateDomBits.find('select').change();
        templateDomBits.children().appendTo('#pd-builddefs > tbody');
        
        // hide the no entries found message
        jQuery('#pd-builddef-empty').hide();
        currentBdefSerial++;
    });

    jQuery('.pd-usources-deleter').click(function () {
            var usourceId = "#" + jQuery(this).parents().get(1).id;
            jQuery(usourceId).remove();
            // show the no entries found if last one removed
            var templateDomBits = jQuery('#pd-usources > tbody').clone(true);
            var numEntries = 0;
            templateDomBits.find('tr').each(function () {
                numEntries += 1;
            });
            if(numEntries <= 1) {
                jQuery('#pd-usources-empty').show();
            }
    });
    
    jQuery('.pd-usources-adder').click(function () {
        currentUsourceSerial++;
        var templateDomBits = jQuery('#pd-usources-bt-all > tbody').clone(true);
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
        templateDomBits.children().appendTo('#pd-usources > tbody');
        
        // hide the no entries found message
        jQuery('#pd-usources-empty').hide();
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
