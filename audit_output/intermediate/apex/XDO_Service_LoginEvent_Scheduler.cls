global with sharing class XDO_Service_LoginEvent_Scheduler implements Schedulable {
    private static final Integer BATCH_SIZE = 200;

    global void execute(SchedulableContext SC) {
        Date today = Date.today();
        Date yesterday = today.addDays(-1);
        Time midnight = Time.newInstance(0, 0, 0, 0);

        Datetime export_start = Datetime.newInstance(yesterday, midnight);
        Datetime export_end = Datetime.newInstance(today, midnight);

        Database.executeBatch(new XDO_Service_LoginEvent_Batch(export_start, export_end), BATCH_SIZE);
    }

    global static void scheduleJob() {
        System.schedule('xDO Service - Tracking Events - Login History', '0 0 0 1/1 * ? *', new XDO_Service_LoginEvent_Scheduler());
    }

    global static void abortJob() {
        List<AsyncApexJob> jobs = [
                SELECT Id,
                        CronTriggerId,
                        Status
                FROM AsyncApexJob
                WHERE ApexClass.Name = 'SchedulableContext'
                AND Status = 'Queued'
        ];

        for (AsyncApexJob job : jobs) {
            System.abortJob(job.CronTriggerId);
        }
    }
}