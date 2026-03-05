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
 * Usage:
 *      // Schedule Tracking Event Sync
 *          new XDO_Tool_QueueableScheduler(new XDO_Tool_TrackingEventSync(new XDO_Tool_TrackingEventService(new XDO_Tool_MixpanelClient())), 'SDO Tool - Synchronise Tracking Events')
 *                  .schedule();
 *
 *          Or with options:
 *
            new XDO_Tool_QueueableScheduler(new xDO_Tool_TrackingEventSyncProfile(new XDO_Tool_TrackingEventService(new XDO_Tool_MixpanelClient(2099781)))
                    .setBatchSize(50), 'jobName')
                    .setScheduleInterval(5)
                    .schedule();
 */

 public class XDO_Tool_QueueableScheduler implements Schedulable {
    public static final Integer SCHEDULE_INTERVAL_MINUTES_DEFAULT = 5;
    public static final Integer SCHEDULE_INTERVAL_MIN = 2;
    public static final Datetime SCHEDULE_START_IMMEDIATELY = System.now().addSeconds(30);

    private XDO_Tool_QueueableBase job {
        get;
        set {
            if (value == null) {
                throw new XDO_Tool_NullOrEmptyArgumentException('job', null);
            }
            this.job = value;
        }
    }

    private String jobName {
        get;
        set {
            if (String.isBlank(value)) {
                throw new XDO_Tool_NullOrEmptyArgumentException('jobName', null);
            }
            this.jobName = value.trim();
        }
    }

    private Integer scheduleInterval {
        get;
        set {
            this.scheduleInterval = (value == null ||
                    value < SCHEDULE_INTERVAL_MIN) ?
                    SCHEDULE_INTERVAL_MINUTES_DEFAULT :
                    value;
        }
    }

    public XDO_Tool_QueueableScheduler(XDO_Tool_QueueableBase job, String jobName) {
        this.scheduleInterval = SCHEDULE_INTERVAL_MINUTES_DEFAULT;
        this.jobName = jobName;
        this.job = job;
    }

    public XDO_Tool_QueueableScheduler setScheduleInterval(Integer scheduleInterval) {
        this.scheduleInterval = scheduleInterval;

        return this;
    }

    public void schedule() {
        schedule(null);
    }

    public void schedule(Datetime scheduleTime) {
        Datetime dt = scheduleTime == null ? SCHEDULE_START_IMMEDIATELY : scheduleTime;
        scheduleJob(this.jobName, dt);
    }

    public XDO_Tool_QueueableScheduler getSchedulableInstance() {
        return this;
    }

    private void rescheduleJob(SchedulableContext context) {
        try {
            System.abortJob(context?.getTriggerId());
            schedule(System.now().addMinutes(this.scheduleInterval));
        } catch (Exception e) {
            // TODO: Raise error?
            System.debug(String.format('>>>>> Error scheduling job {0} with error {1}', new List<String>{
                    this.jobName, e.getMessage()
            }));
        }
    }

    private void scheduleJob(String jobName, Datetime schedule) {
        String cronExpression = String.format('{0} {1} {2} {3} {4} ? {5}', new List<String>{
                String.valueOf(schedule.second()),
                String.valueOf(schedule.minute()),
                String.valueOf(schedule.hour()),
                String.valueOf(schedule.day()),
                String.valueOf(schedule.month()),
                String.valueOf(schedule.year())
        });

        System.schedule(jobName, cronExpression, this.getSchedulableInstance());
    }

    public void execute(SchedulableContext context) {
        try {
            this.job.queue();
        } catch (Exception e) {
            new XDO_Tool_TrackingEventProduct.Error()
                    .setMessage(String.format('{0} : {1}', new List<String>{
                            XDO_Tool_Utilities.getClassName(this), e.getMessage()
                    }))
                    .setAction('XDO_Tool_QueueableScheduler execution error')
                    .setAssetIdentifier(System.Label.xDO_Tool_Tracking_Event_Version)
                    .publish();
        } finally {
            this.rescheduleJob(context);
        }
    }
}