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
 * @date 16/2/2024
 *
 * TODO:
 */

public class XDO_Tool_TrackingEventJobScheduler extends XDO_Tool_QueueableBase //NOPMD
{
    private XDO_Tool_TrackingEventJobSchedulerSvc service;

    /**
     * Constructors
     */
    public XDO_Tool_TrackingEventJobScheduler() {
        setService();
    }

    private class TrackingServiceSchedulingException extends Exception {
    }

    public XDO_Tool_QueueableBase setService() {
        return setService(new XDO_Tool_TrackingEventJobSchedulerSvc()); // Default job scheduling service
    }

    public override XDO_Tool_QueueableBase setService(XDO_Tool_QueueableBase.XDO_Tool_IQueueableService service) {
        this.service = (XDO_Tool_TrackingEventJobSchedulerSvc) service;

        return this;
    }

    public override void execute(System.QueueableContext context) {
        List<xDO_Tool_TrackingEventJob__mdt> jobs = [
                SELECT DeveloperName,
                        Label,
                        Batch_Size__c,
                        Client_Type__c,
                        Entry_Stage__c,
                        Exit_Stage__c,
                        Job_Name__c,
                        Named_Credential__c,
                        Notification_Emails__c,
                        Project_Id__c,
                        Project_Token__c,
                        Project_Name__c,
                        Queueable_Type__c,
                        Schedule_Interval__c
                FROM xDO_Tool_TrackingEventJob__mdt
                WHERE Is_Schedulable__c = TRUE
        ];

        service.scheduleJobs(jobs);
    }

    protected override Boolean shouldChainQueueable() {
        return false;
    }
}