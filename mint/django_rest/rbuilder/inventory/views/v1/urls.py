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


from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.inventory.views.v1 import views as inventoryviews
from mint.django_rest import urls

URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    # Discoverability
    URL(r'/?$', 
        inventoryviews.InventoryService(), 
        name='Inventory'),

    # Log
    URL(r'/log/?$',
        inventoryviews.InventoryLogService(),
        name='Log'),

    # System States
    URL(r'/system_states/?$',
        inventoryviews.InventorySystemStatesService(),
        name='SystemStates'),
    URL(r'/system_states/(?P<system_state_id>\d+)/?$',
        inventoryviews.InventorySystemStateService(),
        name='SystemState'),

    # Zones
    URL(r'/zones/?$',
        inventoryviews.InventoryZonesService(),
        name='Zones'),
    URL(r'/zones/(?P<zone_id>\d+)/?$',
        inventoryviews.InventoryZoneService(),
        name='Zone'),

    # Management Nodes
    URL(r'/management_nodes/?$',
        inventoryviews.InventoryManagementNodesService(),
        name='ManagementNodes',
        model='inventory.ManagementNodes'),
    URL(r'/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryManagementNodeService(),
        name='ManagementNode',
        model='inventory.ManagementNode'),
    URL(r'/zones/(?P<zone_id>\d+)/management_nodes/?$',
        inventoryviews.InventoryZoneManagementNodesService(),
        name='ZoneManagementNodes',
        model='inventory.ZoneManagementNodes'),
    URL(r'/zones/(?P<zone_id>\d+)/management_nodes/(?P<management_node_id>\d+)/?$',
        inventoryviews.InventoryZoneManagementNodeService(),
        name='ZoneManagementNode',
        model='inventory.ZoneManagementNode'),

    # System types
    URL(r'/system_types/?$',
        inventoryviews.InventorySystemTypesService(),
        name='SystemTypes',
        model='inventory.SystemTypes'),
    URL(r'/system_types/(?P<system_type_id>\d+)/?$',
        inventoryviews.InventorySystemTypeService(),
        name='SystemType',
        model='inventory.SystemType'),
    URL(r'/system_types/(?P<system_type_id>\d+)/systems/?$',
        inventoryviews.InventorySystemTypeSystemsService(),
        name='SystemTypeSystems',
        model='inventory.Systems'),
       
    # Networks
    URL(r'/networks/?$',
        inventoryviews.InventoryNetworksService(),
        name='Networks',
        model='inventory.Networks'),
    URL(r'/networks/(?P<network_id>\d+)/?$',
        inventoryviews.InventoryNetworkService(),
        name='Network',
        model='inventory.Network'),

    # Systems
    # RBL-8919 - accept double slashes to accommodate an rpath-tools bug
    URL(r'/systems/?$',
        inventoryviews.InventorySystemsService(),
        name='Systems',
        model='inventory.Systems'),
    URL(r'/inventory_systems/?$',
        inventoryviews.InventoryInventorySystemsService(),
        name='InventorySystems',
        model='inventory.Systems'),
    URL(r'/infrastructure_systems/?$',
        inventoryviews.InventoryInfrastructureSystemsService(),
        name='InfrastructureSystems',
        model='inventory.Systems'),
    URL(r'/systems/(?P<system_id>\d+)/?$',
        inventoryviews.InventorySystemsSystemService(),
        name='System',
        model='inventory.System'),
    URL(r'/systems/(?P<system_id>\d+)/system_log/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLog',
        model='inventory.SystemLog'),
    URL(r'/systems/(?P<system_id>\d+)/jobs/?$',
        inventoryviews.InventorySystemJobsService(),
        name='SystemJobs',
        model='inventory.SystemJobs'),
    URL(r'/systems/(?P<system_id>\d+)/descriptors/(?P<descriptor_type>[_A-Za-z]+)/?$',
        inventoryviews.InventorySystemJobDescriptorService(),
        name='SystemJobDescriptors'),
    URL(r'/systems/(?P<system_id>\d+)/job_states/(?P<job_state_id>[a-zA-Z0-9]+)/jobs/?$',
        inventoryviews.InventorySystemJobStatesService(),
        name='SystemJobStateJobs',
        model='inventory.SystemJobs'),
    URL(r'/systems/(?P<system_id>\d+)/system_events/?$',
        inventoryviews.InventorySystemsSystemEventService(),
        name='SystemsSystemEvent',
        model='inventory.SystemEvents'),
    URL(r'/systems/(?P<system_id>\d+)/system_log/(?P<format>[a-zA-Z]+)/?$',
        inventoryviews.InventorySystemsSystemLogService(),
        name='SystemLogFormat',
        model='inventory.SystemLog'),

    # System Events
    URL(r'/system_events/?$',
        inventoryviews.InventorySystemEventsService(),
        name='SystemEvents',
        model='inventory.SystemEvents'),
    URL(r'/system_events/(?P<system_event_id>\d+)/?$',
        inventoryviews.InventorySystemEventService(),
        name='SystemEvent',
        model='inventory.SystemEvent'),

    # System Tags
    URL(r'/systems/(?P<system_id>\d+)/system_tags/?$',
        inventoryviews.InventorySystemTagsService(),
        name='SystemTags'),
    URL(r'/systems/(?P<system_id>\d+)/system_tags/(?P<system_tag_id>\d+)/?$',
        inventoryviews.InventorySystemTagService(),
        name='SystemTag'),

    # Event Types
    URL(r'/event_types/?$',
        inventoryviews.InventoryEventTypesService(),
        name='EventTypes',
        model='inventory.EventTypes'),
    URL(r'/event_types/(?P<event_type_id>\d+)/?$',
        inventoryviews.InventoryEventTypeService(),
        name='EventType',
        model='inventory.EventType'),

)
