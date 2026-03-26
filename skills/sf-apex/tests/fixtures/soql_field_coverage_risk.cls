public with sharing class SoqlFieldCoverageRisk {
    /**
     * @description Minimal query followed by many field references.
     */
    public static void run() {
        List<Account> accounts = [SELECT Id, Name FROM Account LIMIT 5];
        for (Account a : accounts) {
            System.debug(a.Name);
            System.debug(a.Industry);
            System.debug(a.BillingCity);
            System.debug(a.Phone);
            System.debug(a.Website);
            System.debug(a.Type);
        }
    }
}
