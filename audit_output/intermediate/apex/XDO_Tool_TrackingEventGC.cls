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
 * @date 10/4/2024
 *
 * TODO:
 */

public class XDO_Tool_TrackingEventGC extends XDO_Tool_QueueableBase implements Database.AllowsCallouts //NOPMD
{
    public static final String GC_ERROR_ACTION = 'Scheduled garbage collection execution';
    private XDO_Tool_TrackingEventService service;

    /**
     * Constructors
     */
    public XDO_Tool_TrackingEventGC() {
    }

    public XDO_Tool_TrackingEventGC(XDO_Tool_TrackingEventService service) {
        super();
        this.setService(service);
    }

    public override XDO_Tool_QueueableBase setService(XDO_Tool_IQueueableService service) {
        this.service = (XDO_Tool_TrackingEventService) service;

        return this;
    }

    public override void execute(System.QueueableContext context) {
        try {
            List<XDO_Tool_Tracking_Event__c> events = [
                    SELECT Id
                    FROM XDO_Tool_Tracking_Event__c
                    WHERE Stage__c = :this.config.Entry_Stage__c
                    AND Error__c = ''
                    AND Once__c = FALSE
                    ORDER BY CreatedDate ASC
                    LIMIT :this.batchSize
            ];

            if (!events.isEmpty()) {
                service.deleteEvents(events);
            }
            else {
                events.clear();

                events = [
                        SELECT Id
                        FROM XDO_Tool_Tracking_Event__c
                        WHERE Stage__c = :this.config.Entry_Stage__c
                        AND Error__c = ''
                        ORDER BY CreatedDate ASC
                        LIMIT :this.batchSize
                ];

                service.finalize(events, this.config.Exit_Stage__c);
            }

        } catch (Exception e) {
            new XDO_Tool_TrackingEventProduct.Error()
                    .setMessage(String.format('{0} : {1}', new List<String>{
                            XDO_Tool_Utilities.getClassName(this), e.getMessage()
                    }))
                    .setAction(GC_ERROR_ACTION)
                    .setAssetIdentifier(System.Label.xDO_Tool_Tracking_Event_Version)
                    .publish();
        } finally {
            this.reQueueJob();
        }
    }

    protected override Boolean shouldChainQueueable() {
        return super.shouldChainQueueable() &&
                [
                        SELECT COUNT()
                        FROM XDO_Tool_Tracking_Event__c
                        WHERE Stage__c = :this.config.Entry_Stage__c
                        AND Error__c = ''
                ] > 0;
    }
}