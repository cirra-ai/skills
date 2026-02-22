/**
 * @description Batch Apex class that finds all Accounts where AnnualRevenue
 *              is null and sets it to 0. Tracks processed/failed counts.
 * @author      CirraTest
 * @date        2025-01-15
 */
public with sharing class CirraTest_AccountRevenueBatch
    implements Database.Batchable<SObject>, Database.Stateful {

    private Integer processedCount = 0;
    private Integer failedCount = 0;
    private List<String> errorMessages = new List<String>();

    /**
     * @description Start method returns QueryLocator for Accounts with null revenue.
     * @param bc BatchableContext.
     * @return Database.QueryLocator for the batch query.
     */
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name, AnnualRevenue
            FROM Account
            WHERE AnnualRevenue = null
            WITH USER_MODE
        ]);
    }

    /**
     * @description Execute method updates AnnualRevenue to 0.
     * @param bc BatchableContext.
     * @param scope List of Account records in this batch.
     */
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account acc : scope) {
            acc.AnnualRevenue = 0;
        }
        List<Database.SaveResult> results = Database.update(scope, false);
        for (Database.SaveResult sr : results) {
            if (sr.isSuccess()) {
                processedCount++;
            } else {
                failedCount++;
                for (Database.Error err : sr.getErrors()) {
                    errorMessages.add(
                        'Record ' + sr.getId() + ': ' + err.getMessage()
                    );
                }
            }
        }
    }

    /**
     * @description Finish method sends email summary of batch results.
     * @param bc BatchableContext.
     */
    public void finish(Database.BatchableContext bc) {
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new String[]{ UserInfo.getUserEmail() });
        email.setSubject('Account Revenue Batch Complete');
        email.setPlainTextBody(
            'Batch Complete\n' +
            'Processed: ' + processedCount + '\n' +
            'Failed: ' + failedCount + '\n' +
            (errorMessages.isEmpty() ? '' : 'Errors:\n' + String.join(errorMessages, '\n'))
        );
        Messaging.sendEmail(new Messaging.SingleEmailMessage[]{ email });
    }
}
