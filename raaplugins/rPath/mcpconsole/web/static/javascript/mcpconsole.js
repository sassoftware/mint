function doHide(button)
{
    var summaryRow = button;
    while(summaryRow.tagName != "TR") // Recurse up the tree to our TR
        summaryRow = summaryRow.parentNode;

    var detailRow = summaryRow.nextSibling;
    while(detailRow.tagName != "TR") // Skip over text nodes...
        detailRow = detailRow.nextSibling;

    detailCell = detailRow.getElementsByTagName("TD")[0];
    if(hasElementClass(detailCell, "hidden")) {
        removeElementClass(detailCell, "hidden");
        replaceChildNodes(button, "-");
    } else {
        addElementClass(detailCell, "hidden");
        replaceChildNodes(button, "+");
    }
}

