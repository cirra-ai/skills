/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */

/**
 * @author Paul Lucas
 * @company       Salesforce
 *
 * @date 5/1/2024
 *
 * TODO:
 */
public virtual without sharing class XDO_Tool_TrackingEventService implements XDO_Tool_QueueableBase.XDO_Tool_IQueueableService //NOPMD
{
    private static final String DML_FAILED_TO_UPDATE_EVENTS_MESSAGE = '>>>>> {0}: Failed to update events because {1}';
    private static final String DML_FAILED_TO_DELETE_EVENTS_MESSAGE = '>>>>> {0}: Failed to delete events because {1}';

    private XDO_Tool_TrackingEventClient client;

    /**
     * Constructors
     */
    public XDO_Tool_TrackingEventService() {
    }

    public XDO_Tool_TrackingEventService(XDO_Tool_TrackingEventClient client) {
        this.client = client;
    }

    public abstract class XDO_Tool_TrackingEventClient extends XDO_Tool_ApiService.Client {
        public XDO_Tool_TrackingEventClient() {
        }

        public XDO_Tool_TrackingEventClient(String namedCredential) {
            super(namedCredential);
        }

        protected virtual override void handleError(XDO_Tool_ApiService.ApiServiceResponse response) {
            // Common error handler
        }

        protected virtual override void handleResponse(Object response) {
            // Common response handler
        }

        public abstract XDO_Tool_TrackingEventClient transformEvents(List<XDO_Tool_Tracking_Event__c> events);
        public abstract XDO_Tool_TrackingEventClient importEvents();
        public abstract List<XDO_Tool_Tracking_Event__c> processResults(List<XDO_Tool_Tracking_Event__c> events);

        public abstract XDO_Tool_TrackingEventClient transformProfiles(List<XDO_Tool_Tracking_Event__c> events);
        public abstract XDO_Tool_TrackingEventClient setProfiles();
    }

    /**
     * resetErrors: Clear previous errors
     *
     * @param trackingEvents : List of XDO_Tool_Tracking_Event__c
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService resetEvents(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
        for (XDO_Tool_Tracking_Event__c event : trackingEvents) {
            event.Error__c = '';
        }

        return this;
    }

    /**
     * transformEvents: Transform event message depending on client
     *
     * @param trackingEvents
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService transformEvents(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
        this.client.transformEvents(trackingEvents);

        return this;
    }

    /**
     * transformProfiles: Transform profile message depending on client
     *
     * @param trackingEvents
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService transformProfiles(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
        this.client.transformProfiles(trackingEvents);

        return this;
    }

    /**
     * loadEvents : Load events into the target system
     *
     * @param trackingEvents
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService loadEvents(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
        this.client.importEvents()
                .processResults(trackingEvents);

        return this;
    }

    /**
     * loadProfiles : Load profiles into the target system
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService loadProfiles() {
        this.client.setProfiles();

        return this;
    }

    /**
     * finalize: Complete processing for this batch
     *
     * @param trackingEvents : List of XDO_Tool_Tracking_Event__c
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService finalize(List<XDO_Tool_Tracking_Event__c> trackingEvents, String stage) {
        if (trackingEvents.size() > 0) {
            for (XDO_Tool_Tracking_Event__c event : trackingEvents) {
                event.Stage__c = stage;
            }

            try {
                UPDATE trackingEvents;
            } catch (DmlException e) {
                System.debug(String.format(DML_FAILED_TO_UPDATE_EVENTS_MESSAGE, new List<String>{
                        XDO_Tool_Utilities.getClassName(this), e.getMessage()
                }));
            }
        }

        return this;
    }

    /**
     * deleteEvents: Remove processed events
     *
     * @param trackingEvents : List of XDO_Tool_Tracking_Event__c
     *
     * @return
     */
    public virtual XDO_Tool_TrackingEventService deleteEvents(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
        if (trackingEvents.size() > 0) {
            try {
                DELETE trackingEvents;
            } catch (DmlException e) {
                System.debug(String.format(DML_FAILED_TO_DELETE_EVENTS_MESSAGE, new List<String>{
                        XDO_Tool_Utilities.getClassName(this), e.getMessage()
                }));
            }
        }

        return this;
    }
}