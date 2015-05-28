<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
 o Click 'Appliances'
 o Click 'Appliances I own/develop'
 o Click on the ${projectName} appliance
 o Click on the orange drop down 'Action' menu on the right.  Select 
   'Manage membership'
 o You can find all outstanding requests under the 'Requestors' heading at
   the bottom of the page.</plain>
