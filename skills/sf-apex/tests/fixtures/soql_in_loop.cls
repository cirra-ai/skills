public with sharing class BadSoqlInLoop {
    /**
     * @description Purposely bad pattern used as validator fixture.
     */
    public static void run(List<Id> accountIds) {
        for (Id accountId : accountIds) {
            Account a = [SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1];
            System.debug(a.Name);
        }
    }
}
