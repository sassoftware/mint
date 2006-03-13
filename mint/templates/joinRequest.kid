<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns#">
A user of ${cfg.productName} would like to join a project you own:

${name} would like to join ${projectName}.
<p py:if="displayEmail">Contact Information: ${displayEmail}</p>
<p py:if="comments">Comments: ${comments}</p>
<p py:if="not comments">No comments were supplied.</p>
To respond to this request:

 o Login to ${cfg.productName}.
 o Click on the 'Requests Pending' link under the 'My Projects' sidebar.
    (Note: This link will not be present if the user retracted their request
     or another project owner has already responded to it.)
 o You can find all outstanding requests under the 'Requestors' heading at
   the bottom of the page.</plain>
