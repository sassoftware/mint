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


from mint.django_rest.rbuilder.modellib import basemodels

class UserManager(basemodels.BaseManager):
    def load_from_object(self, xobjModel, request, flags=None):
        # We absolutely don't want the model to be saved, we'll let the
        # old rbuilder interface handle the saving
        return basemodels.BaseManager.load_from_object(self,
            xobjModel, request, flags=flags.copy(save=False))
