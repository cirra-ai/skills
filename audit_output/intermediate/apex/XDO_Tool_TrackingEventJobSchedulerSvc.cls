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
 * @date 19/2/2024
 *
 * TODO:
 */

public virtual without sharing class XDO_Tool_TrackingEventJobSchedulerSvc implements XDO_Tool_QueueableBase.XDO_Tool_IQueueableService //NOPMD
{
    private static final String PROJECT_ID = 'projectId';
    private static final String PROJECT_TOKEN = 'projectToken';

    private static final String SCHEDULE_JOB_FAILED_MESSAGE = '{0} failed to schedule in org {1}';
    private static final String SCHEDULE_JOB_SUCCEEDED_MESSAGE = '{0} was restarted in org {1}';
    private static final String TYPES_COULD_NOT_BE_INSTANTIATED_MESSAGE = 'The following type(s) could not be instantiated: {0}';

    public enum CRONTRIGGER_FIELD {
        JobId,
        State
    }

    public enum CRONTRIGGER_STATE {
        DELETED
    }

    String message, jobName;
    List<String> undefinedTypes = new List<String>();
    Type clientType, queueableType;
    XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient client;
    XDO_Tool_QueueableBase queueable;

    /**
     * Constructors
     */
    public XDO_Tool_TrackingEventJobSchedulerSvc() {
    }

    private class TrackingServiceSchedulingException extends Exception {
    }

    /**
     * scheduleJobs : Schedule jobs defined in xDO_Tool_TrackingEventJob__mdt
     *
     * @param jobs
     */
    public void scheduleJobs(List<xDO_Tool_TrackingEventJob__mdt> jobs) {
        Map<String, SObject> scheduledJobs = new Map<String, SObject>([
                SELECT CronJobDetail.Name Id,
                        Id JobId,
                        State
                FROM CronTrigger
                GROUP BY CronJobDetail.Name, Id, State
        ]);

        for (xDO_Tool_TrackingEventJob__mdt job : jobs) {
            jobName = String.format(job.Job_Name__c, new List<String>{
                    job.Project_Name__c, job.Project_Id__c
            });

            if (!scheduledJobs.containsKey(jobName) ||
                    scheduledJobs.get(jobName).get(CRONTRIGGER_FIELD.State.name()) == CRONTRIGGER_STATE.DELETED.name()) {

// TODO: Store last schedule attempt
//                job.Last_Notification_Time__c = Datetime.now();
//                CustomMetadata.Operations
//                        .callback(new CustomMetadata.DebugCallback())
//                        .enqueueUpsertRecords(
//                                new List<SObject>{
//                                        job
//                                });

                try {
                    if (scheduledJobs.containsKey(jobName)) {
                        System.abortJob(scheduledJobs.get(jobName).get(CRONTRIGGER_FIELD.JobId.name()).toString());
                    }

                    clientType = Type.forName(job.Client_Type__c);
                    queueableType = Type.forName(job.Queueable_Type__c);

                    if (clientType == null) {
                        undefinedTypes.add(job.Client_Type__c);
                    }

                    if (queueableType == null) {
                        undefinedTypes.add(job.Queueable_Type__c);
                    }
                    if (!undefinedTypes.isEmpty()) {
                        throw new TrackingServiceSchedulingException(String.format(TYPES_COULD_NOT_BE_INSTANTIATED_MESSAGE, new List<String>{
                                String.join(undefinedTypes, ', ')
                        }));
                    }

                    client = (XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient) clientType.newInstance();
                    queueable = (XDO_Tool_QueueableBase) queueableType.newInstance();

                    client.initialize(new Map<String, String>{
                            PROJECT_ID => job.Project_Id__c ?? '',
                            PROJECT_TOKEN => job.Project_Token__c ?? ''
                    }).setNamedCredential(job.Named_Credential__c ?? '');

                    new XDO_Tool_QueueableScheduler(queueable
                            .setService(new XDO_Tool_TrackingEventService(client))
                            .setBatchSize(Integer.valueOf(job.Batch_Size__c))
                            .setConfig(job), jobName)
                            .setScheduleInterval(Integer.valueOf(job.Schedule_Interval__c))
                            .schedule();

                    message = String.format(SCHEDULE_JOB_SUCCEEDED_MESSAGE, new List<String>{
                            jobName, UserInfo.getOrganizationId()
                    });
                    XDO_Tool_Utilities.sendMail(job.Notification_Emails__c, message, message);

                } catch (Exception e) {
                    undefinedTypes.clear();

                    message = String.format(SCHEDULE_JOB_FAILED_MESSAGE, new List<String>{
                            jobName, UserInfo.getOrganizationId()
                    });

                    System.debug(String.format('Exception message: {0} \r\n\r\n Job Config: {1}', new List<String>{
                            e.getMessage(), JSON.serializePretty(job)
                    }));

                    XDO_Tool_Utilities.sendMail(job.Notification_Emails__c, message, String.format('Exception message: {0} \r\n\r\n Job Config: {1}  \r\n\r\n Username: {2}', new List<String>{
                            e.getMessage(), JSON.serializePretty(job), System.UserInfo.getUserName()
                    }));
                }
            }
        }
    }
}