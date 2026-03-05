public with sharing class QuickAccountLookupController {

    @AuraEnabled(cacheable=true)
    public static List<Account> searchAccounts(String searchTerm) {
        try {
            String searchKey = String.isNotBlank(searchTerm)
                ? '%' + String.escapeSingleQuotes(searchTerm) + '%'
                : '%';

            return [
                SELECT Id, Name, Industry, Phone, AnnualRevenue
                FROM Account
                WHERE Name LIKE :searchKey
                WITH SECURITY_ENFORCED
                ORDER BY Name
                LIMIT 20
            ];
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}