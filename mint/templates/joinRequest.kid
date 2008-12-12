<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2008 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import projectText
?>
<plain xmlns:py="http://purl.org/kid/ns#">
A user of ${cfg.productName} would like to become a developer on a ${projectText().lower()} you own:

${name} would like to become a developer on ${projectName}.
<p py:if="displayEmail">Contact Information: ${displayEmail}</p>
<p py:if="comments">Comments: ${comments}</p>
<p py:if="not comments">No comments were supplied.</p>
To respond to this request:

 o Login to ${cfg.productName}.
 o Select ${projectName} from the 'Pending requests' dropdown menu
   within the right-hand sidebar.
     (Note: ${projectName} may not be present in the dropdown menu
     if the user has retracted their request or another ${projectText().lower()}
     owner has already responded to it.)
 o You can find all outstanding requests under the 'Requestors' heading at
   the bottom of the page.</plain>
