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
 * @date 22/12/2023
 *
 * TODO:
 */

public class XDO_Tool_TrackingEventSync extends XDO_Tool_QueueableBase implements Database.AllowsCallouts //NOPMD
{
    private XDO_Tool_TrackingEventService service;

    /**
     * Constructors
     */
    public XDO_Tool_TrackingEventSync() {
    }

    public XDO_Tool_TrackingEventSync(XDO_Tool_TrackingEventService service) {
        super();
        this.setService(service);
    }

    public override XDO_Tool_QueueableBase setService(XDO_Tool_IQueueableService service) {
        this.service = (XDO_Tool_TrackingEventService) service;

        return this;
    }

    public override void execute(System.QueueableContext context) {
        List<XDO_Tool_Tracking_Event__c> events = [
                SELECT Type__c,
                        Event__c,
                        Event_Date__c,
                        Email__c,
                        Payload__c,
                        Unique_Id__c,
                        CreatedDate,
                        Stage__c
                FROM XDO_Tool_Tracking_Event__c
                WHERE Stage__c = :this.config.Entry_Stage__c
                ORDER BY CreatedDate ASC
                LIMIT :this.batchSize
        ];

        service.resetEvents(events)
                .transformEvents(events)
                .loadEvents(events)
                .finalize(events, this.config.Exit_Stage__c);

        this.reQueueJob();
    }

    protected override Boolean shouldChainQueueable() {
        return super.shouldChainQueueable() &&
                [
                        SELECT COUNT()
                        FROM XDO_Tool_Tracking_Event__c
                        WHERE Stage__c = :this.config.Entry_Stage__c
                ] > 0;
    }
}