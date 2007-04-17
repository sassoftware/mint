/*
 Copyright (c) 2007 rPath Inc.
 All rights reserved
*/

var filesystems = new Array();
var uniqId = 0;

// some default mount points
var defaultMountPoints = ['/', '/home', '/srv', '/tmp', '/usr', '/var'];
var mountPointsDS = new YAHOO.widget.DS_JSArray(defaultMountPoints);

var fsTypes = ['ext3', 'swap'];

function FilesystemRow(baseId) {
    logDebug("baseId: " + baseId);
    this.baseId = baseId;
    bindMethods(this);
}

FilesystemRow.prototype.baseId = null;
FilesystemRow.prototype.mountPoint = null;
FilesystemRow.prototype.reqSize = null;
FilesystemRow.prototype.freeSpace = null;
FilesystemRow.prototype.fsType = null;

FilesystemRow.prototype.mountPointEl = null;
FilesystemRow.prototype.reqSizeEl = null;
FilesystemRow.prototype.freeSpaceEl = null;
FilesystemRow.prototype.fsTypeEl = null;

FilesystemRow.prototype.createEditor = function() {
    var typeDD = SELECT({'id': this.baseId + 'FsType', 'class': 'fsTypeDD'});
    for(var i in fsTypes) {
        var fsType = fsTypes[i];
        var attribs = {'value': fsType};
        if(fsType == this.fsType)
            attribs['selected'] = 'selected';
        appendChildNodes(typeDD, OPTION(attribs, fsType));
    }

    // save button
    saveButton = BUTTON({'type': 'button'}, "Save");
    connect(saveButton, "onclick", this.saveRow);

    // delete button
    delButton = BUTTON({'type': 'button'}, "X");
    connect(delButton, "onclick", this.deleteRow);

    this.mpInputEl = INPUT({'id': this.baseId + 'MpInput', 'class': 'MpInput', 'size': 6, 'type': 'text', 'value': this.mountPoint});
    this.reqSizeEl = INPUT({'size': 6, 'type': 'text', 'value': this.reqSize});
    this.freeSpaceEl = INPUT({'id': this.baseId + 'FreeSpaceEl', 'size': 6, 'type': 'text', 'value': this.freeSpace});
    this.fsTypeEl = typeDD;

    this.fsTypeChosen();
    connect(typeDD, "onchange", this.fsTypeChosen);

    var el = TR({'id': this.baseId + 'Editor'},
        TD(null, DIV({'class': 'mpAutoComplete'}, this.mpInputEl, DIV({'id': this.baseId + 'MpContainer', 'class': 'MpContainer'}))),
        TD(null, DIV({'id': this.baseId + 'sliderBg', 'class': 'sliderBg'},
                 DIV({'id': this.baseId + 'sliderThumb'},
                 IMG({'src': 'http://developer.yahoo.com/yui/examples/slider/img/horizSlider.png'})))
        ),
        TD(null, this.freeSpaceEl),
        TD(null, typeDD),
        TD(null, saveButton),
        TD(null, delButton)
    );

    // free space slider
    this.freeSpaceSlider = YAHOO.widget.Slider.getHorizSlider(this.baseId + 'sliderBg', this.baseId + 'sliderThumb', 0, 120);
    this.freeSpaceSlider.setValue(this.freeSpace/64);
    this.freeSpaceEl.value = this.freeSpace;

    var freeSpaceEl = this.freeSpaceEl;
    this.freeSpaceSlider.subscribe("change", function(newVal) {
        freeSpaceEl.value = newVal*64;
    });

    return el;
}

FilesystemRow.prototype.prepareAutoComplete = function() {
    var mpInputEl = this.mpInputEl;
    var mountPointEl = new YAHOO.widget.AutoComplete(this.baseId + 'MpInput', this.baseId + 'MpContainer', mountPointsDS);
    mountPointEl.queryDelay = 0;
    mountPointEl.prehighlightClassName = "yui-ac-prehighlight";
    mountPointEl.useShadow = false;
    mountPointEl.minQueryLength = 0;
    mountPointEl.textboxFocusEvent.subscribe(function(){mountPointEl.sendQuery("");});
    this.mountPointEl = mountPointEl;
}

FilesystemRow.prototype.editRow = function() {
    var editor = this.createEditor();
    swapDOM($(this.baseId + 'Filesystem'), editor);
    this.prepareAutoComplete();
}

FilesystemRow.prototype.createStaticRow = function() {
    var editButton = BUTTON({'type': 'button'}, "Edit");
    var callback = function() {
        this.editRow();
    }
    connect(editButton, "onclick", bind(callback, this));

    var row = TR({'id': this.baseId + 'Filesystem'},
        TD(null, this.mountPoint),
        TD({'colspan': 2}, this.freeSpace),
        TD(null, this.fsType),
        TD(null, editButton)
    );
    return row;
}

FilesystemRow.prototype.saveRow = function() {
    var editor = $(this.baseId + 'Editor');

    this.mountPoint = this.mpInputEl.value;
    this.reqSize = this.reqSizeEl.value;
    this.freeSpace = this.freeSpaceEl.value;
    this.fsType = this.fsTypeEl.options[this.fsTypeEl.selectedIndex].value;

    row = this.createStaticRow();
    swapDOM(editor, row);
}

FilesystemRow.prototype.deleteRow = function() {
    logDebug("deleting row: " + this);
    removeElement($(this.baseId + "Editor"));

    var index = -1;
    for(var i in filesystems)
        if(filesystems[i] == this)
            index = i;

    if(index > 0) {
        filesystems.splice(index, 1);
    }
}

FilesystemRow.prototype.fsTypeChosen = function() {
    var curFsType = this.fsTypeEl.options[this.fsTypeEl.selectedIndex].value;

    // swap doesn't need a mount point
    if(curFsType == "swap") {
        this.mpInputEl.value = "none";
        this.mpInputEl.disabled = true;
    } else {
        this.mpInputEl.disabled = false;
    }
}

function addFilesystem() {
    uniqId++;
    var fs = new FilesystemRow("_" + uniqId.toString());
    appendChildNodes($('fsEditorBody'), fs.createEditor());
    fs.prepareAutoComplete();

    filesystems = filesystems.concat(fs);
    logDebug(filesystems);
}

function addPredefinedFilesystem(mountPoint, reqSize, freeSpace, fsType) {
    uniqId++;
    var fs = new FilesystemRow("_" + uniqId.toString());
    fs.mountPoint = mountPoint;
    fs.reqSize = reqSize;
    fs.freeSpace = freeSpace;
    fs.fsType = fsType;
    appendChildNodes($('fsEditorBody'), fs.createStaticRow());

    filesystems = filesystems.concat(fs);
}
